"""
summarizer.py - Agent 2: Brochure Summarization Agent (Demo Mode - Fast, No Chroma)

What it does:
- Loads chunks from a job's chunks.jsonl file (inside jobss/<job_id>/)
- Uses OpenAI GPT model (gpt-4o-mini) to generate structured brochure JSON
- Saves output as brochure.json in the same job folder

Usage:
    python summarizer.py --job_id 20251027_232025_bc7521ff
"""

import os
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

class BrochureSummarizer:
    """Fast summarizer for brochure content using GPT model."""

    def __init__(self, model: str = "gpt-4o-mini", max_tokens: int = 4000):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY not found in environment variables")

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [summarizer] ✅ Initialized with model: {model}")

    def load_chunks(self, file_path: str):
        """Load chunks safely from JSONL file."""
        chunks = []
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Chunks file not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    chunks.append(json.loads(line.strip()))
                except json.JSONDecodeError as e:
                    print(f"[summarizer] ⚠️ Skipping malformed line {line_num}: {e}")

        print(f"[summarizer] 📄 Loaded {len(chunks)} chunks from {file_path}")
        return chunks

    def prepare_context(self, chunks, max_chars: int = 50000) -> str:
        """Combine chunks into a single context (limited by character count)."""
        context_parts = []
        total_chars = 0
        for i, chunk in enumerate(chunks):
            text = chunk.get("text", "")
            if not text.strip():
                continue

            chunk_text = f"--- Chunk {i+1} ---\n{text}\n"
            if total_chars + len(chunk_text) > max_chars:
                context_parts.append(chunk_text[: max_chars - total_chars])
                break

            context_parts.append(chunk_text)
            total_chars += len(chunk_text)

        print(f"[summarizer] 🧩 Prepared context of {total_chars} characters from {len(context_parts)} chunks")
        return "\n".join(context_parts)

    def generate_brochure(self, chunks):
        """Generate structured brochure content directly from chunks."""
        if not chunks:
            raise ValueError("No chunks available for summarization")

        context = self.prepare_context(chunks)
        prompt = f"""
You are a professional brochure writer and marketing expert. 
Based on the following text content, create a clear, professional, and engaging brochure with these sections:

1. Title (max 10 words)
2. Subtitle (max 15 words)
3. Introduction Summary (3-4 sentences)
4. Key Product Features (4-6 items)
5. Competitive Advantages (4-6 items)
6. How It Works (3-5 steps)
7. Additional Insights (other relevant info)

Ensure the output is **valid JSON only**, following this structure:
{{
    "title": "<Title>",
    "subtitle": "<Subtitle>",
    "intro_summary": "<Intro paragraph>",
    "key_features": [
        {{"feature": "<Feature>", "description": "<Description>"}}
    ],
    "competitive_advantages": [
        {{"advantage": "<Advantage>", "explanation": "<Explanation>"}}
    ],
    "how_it_works": [
        {{"step": 1, "title": "<Step title>", "description": "<Description>"}}
    ],
    "additional_insights": "<Additional info>"
}}

Document Content:
{context}
"""

        print(f"[summarizer] 🧠 Generating brochure using {self.model}...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional brochure writer. "
                            "Always return output strictly as valid JSON only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            brochure = json.loads(content)

            brochure["_metadata"] = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model": self.model,
                "chunks_processed": len(chunks),
            }

            print(f"[summarizer] ✅ Brochure generated successfully ({len(content)} characters)")
            return brochure

        except json.JSONDecodeError as e:
            print(f"[summarizer] ❌ Invalid JSON in model response: {e}")
            raise
        except Exception as e:
            print(f"[summarizer] ❌ Error generating brochure: {e}")
            raise

    def save_brochure(self, brochure, output_path: str):
        """Save brochure JSON output."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(brochure, f, indent=2, ensure_ascii=False)

        print(f"[summarizer] 💾 Saved brochure JSON to {output_path}")


def run_summarizer(job_id: str, jobs_root: str = "./jobss"):
    """Main summarizer workflow."""
    job_dir = Path(jobs_root) / job_id
    chunks_path = job_dir / "chunks.jsonl"
    output_path = job_dir / "brochure.json"

    print(f"[summarizer] 🚀 Starting summarization for job: {job_id}")
    print(f"[summarizer] 🔍 Reading chunks from: {chunks_path}")
    print(f"[summarizer] 💾 Will save JSON to: {output_path}")

    summarizer = BrochureSummarizer(model="gpt-4o-mini")
    chunks = summarizer.load_chunks(chunks_path)
    brochure = summarizer.generate_brochure(chunks)
    summarizer.save_brochure(brochure, output_path)

    print(f"\n[summarizer] {'='*60}")
    print(f"[summarizer] ✅ Brochure generation complete!")
    print(f"[summarizer] Title: {brochure.get('title', 'N/A')}")
    print(f"[summarizer] Features: {len(brochure.get('key_features', []))}")
    print(f"[summarizer] Advantages: {len(brochure.get('competitive_advantages', []))}")
    print(f"[summarizer] Steps: {len(brochure.get('how_it_works', []))}")
    print(f"[summarizer] {'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent 2 - Brochure Summarization")
    parser.add_argument("--job_id", required=True, help="Job ID inside jobss/<job_id>/")

    args = parser.parse_args()
    run_summarizer(job_id=args.job_id)
