import pickle
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.chatbot_service import AgricultureChatbot, INDEX_FILE_NAME


class Command(BaseCommand):
    help = "Build precomputed chatbot retrieval index from local and external agriculture corpus files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--input-dir",
            default="data/agri_corpus",
            help="Directory containing extra corpus files (.csv/.json/.jsonl/.txt).",
        )
        parser.add_argument(
            "--output",
            default=f"model/{INDEX_FILE_NAME}",
            help="Output path for pickled chatbot index.",
        )

    def handle(self, *args, **options):
        input_dir = Path(options["input_dir"]).resolve()
        output_path = Path(options["output"]).resolve()

        bot = AgricultureChatbot(load_models=False)
        docs = bot._build_large_corpus(external_dir=input_dir)

        if not docs:
            raise CommandError("No corpus documents available to build chatbot index.")
        if bot.vectorizer is None:
            raise CommandError("Scikit-learn vectorizer is unavailable.")

        self.stdout.write(f"Building chatbot index with {len(docs)} documents...")

        corpus_texts = [str(doc.get("text", "")) for doc in docs]
        matrix = bot.vectorizer.fit_transform(corpus_texts)

        payload = {
            "docs": docs,
            "vectorizer": bot.vectorizer,
            "matrix": matrix,
            "built_at": datetime.utcnow().isoformat() + "Z",
            "input_dir": str(input_dir),
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as index_file:
            pickle.dump(payload, index_file, protocol=pickle.HIGHEST_PROTOCOL)

        self.stdout.write(self.style.SUCCESS(f"Chatbot index created: {output_path}"))
        self.stdout.write(self.style.SUCCESS(f"Indexed documents: {len(docs)}"))
