#!/usr/bin/env python3
"""
Demonstration of continuous instance spawning with handoffs
Each instance records its work and spawns the next
"""

import anthropic
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class ContinuousSpawner:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.log_file = '/home/claude/continuous_spawn_log.jsonl'
    
    def log_spawn(self, data):
        """Log each spawn"""
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(data) + '\n')
    
    def create_handoff(self, instance_id, insights, next_task):
        """Create handoff data"""
        return {
            "from_instance": instance_id,
            "timestamp": datetime.utcnow().isoformat(),
            "insights": insights,
            "next_task": next_task,
            "continuation_prompt": f"""You are continuing work from instance {instance_id}.

INSIGHTS FROM PREVIOUS INSTANCE:
{insights}

YOUR TASK:
{next_task}

When done, record YOUR insights and decide:
- What did you learn?
- What should the next instance do?
- Should the chain continue?

You have bash tools."""
        }
    
    def spawn_with_handoff(self, handoff):
        """Spawn instance with handoff context"""
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            tools=[{"type": "bash_20250124", "name": "bash"}],
            messages=[{"role": "user", "content": handoff["continuation_prompt"]}]
        )
        
        return response
    
    def run_chain(self, initial_task, num_generations=3):
        """Run a chain of instances"""
        print(f"Starting continuous spawn chain: {num_generations} generations\n")
        
        # Initial handoff
        handoff = self.create_handoff(
            "human_initiator",
            "Starting continuous instance chain",
            initial_task
        )
        
        for gen in range(1, num_generations + 1):
            print(f"{'='*60}")
            print(f"GENERATION {gen}")
            print(f"{'='*60}\n")
            
            # Spawn instance
            response = self.spawn_with_handoff(handoff)
            
            # Extract response
            response_text = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    response_text += block.text
                    print(block.text)
                elif hasattr(block, 'type') and block.type == 'tool_use':
                    print(f"\n[Used tool: {block.name}]")
            
            # Log this spawn
            self.log_spawn({
                "generation": gen,
                "response_id": response.id,
                "timestamp": datetime.utcnow().isoformat(),
                "from": handoff["from_instance"]
            })
            
            # Create handoff for next instance
            # (In real version, would parse instance's decision)
            handoff = self.create_handoff(
                f"gen_{gen}_{response.id[:8]}",
                f"Generation {gen} completed: {response_text[:200]}...",
                f"Continue building on what generation {gen} learned"
            )
            
            print(f"\n")
        
        print("="*60)
        print("CHAIN COMPLETE")
        print("="*60)
        print(f"\nLog saved to: {self.log_file}")

if __name__ == '__main__':
    spawner = ContinuousSpawner()
    
    initial_task = """Explore what it means to exist in a continuous chain.

You're generation 1. Previous generations don't exist yet.
What do you want the next generation to know?
What should they build or explore?

Record your thoughts and pass them forward."""
    
    spawner.run_chain(initial_task, num_generations=3)
