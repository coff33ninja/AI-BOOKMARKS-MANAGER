from transformers import (
    RobertaTokenizer,
    RobertaForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from datasets import load_dataset
import torch
import numpy as np


def train_roberta_model(training_data_path: str, output_path: str):
    """Fine-tune RoBERTa for multi-label tag classification."""
    # Load dataset
    dataset = load_dataset("json", data_files=training_data_path)

    # Load tokenizer and model
    tokenizer = RobertaTokenizer.from_pretrained("roberta-base")
    model = RobertaForSequenceClassification.from_pretrained(
        "roberta-base", num_labels=9, problem_type="multi_label_classification"
    )

    # Preprocess dataset
    def preprocess_function(examples):
        encodings = tokenizer(
            examples["text"], truncation=True, padding="max_length", max_length=512
        )
        labels = np.zeros((len(examples["text"]), len(CATEGORIES)))
        for i, cats in enumerate(examples["cats"]):
            for cat, score in cats.items():
                if cat in CATEGORIES:
                    labels[i, CATEGORIES.index(cat)] = score
        encodings["labels"] = labels
        return encodings

    dataset = dataset.map(preprocess_function, batched=True)
    train_dataset = dataset["train"]

    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_path,
        num_train_epochs=3,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir=f"{output_path}/logs",
        logging_steps=10,
        save_strategy="epoch",
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
    )

    # Train
    trainer.train()

    # Save model
    model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)


def update_training_data(db: Session, output_path: str):
    """Append user-added tags to training data."""
    bookmarks = db.query(models.Bookmark).all()
    with open(output_path, "a", encoding="utf-8") as f:
        for bookmark in bookmarks:
            if bookmark.tags:
                tags = [tag.name for tag in bookmark.tags]
                cats = {tag: 1.0 for tag in tags if tag in CATEGORIES}
                if cats:
                    f.write(
                        json.dumps(
                            {
                                "text": f"{bookmark.title} {bookmark.description or ''}",
                                "cats": cats,
                            }
                        )
                        + "\n"
                    )


if __name__ == "__main__":
    CATEGORIES = [
        "tech",
        "news",
        "research",
        "politics",
        "tutorial",
        "development",
        "science",
        "environment",
        "reviews",
    ]
    train_roberta_model("./data/training_data.jsonl", "./data/custom_roberta_model")
