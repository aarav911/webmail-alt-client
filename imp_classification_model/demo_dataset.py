#!/usr/bin/env python3
"""Inspect manually labeled email records and fit a tiny local ML demo."""

import argparse
import base64
import hashlib
import html
import json
import math
import re
import sys
from collections import Counter, defaultdict
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path

LABELS = ("important", "not_important")
TOKEN_RE = re.compile(r"[^\W_]{2,}", re.UNICODE)


class TextOnlyHTMLParser(HTMLParser):
    """Extract visible text without loading resources or executing markup."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def get_message_text(message):
    """Collect non-attachment text parts from an email message."""
    text_parts = []
    for part in message.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get_content_disposition() == "attachment":
            continue

        content_type = part.get_content_type()
        if content_type not in ("text/plain", "text/html"):
            continue

        try:
            content = part.get_content()
        except (LookupError, UnicodeError, ValueError) as error:
            print(
                f"Warning: could not decode a {content_type} body part: {error}",
                file=sys.stderr,
            )
            continue

        if not isinstance(content, str):
            continue
        if content_type == "text/html":
            parser = TextOnlyHTMLParser()
            parser.feed(content)
            content = " ".join(parser.parts)
            content = html.unescape(content)
        text_parts.append(content)

    return "\n\n".join(text_parts)


def load_records(path):
    """Load, validate, decode, and parse each JSONL example."""
    records = []
    with path.open(encoding="utf-8") as dataset:
        for line_number, line in enumerate(dataset, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                label = record["classification"]
                if label not in LABELS:
                    raise ValueError(f"unsupported classification {label!r}")
                if record["raw_email_encoding"] != "base64":
                    raise ValueError("raw_email_encoding must be 'base64'")
                raw = base64.b64decode(record["raw_email"], validate=True)
                message = BytesParser(policy=policy.default).parsebytes(raw)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                raise ValueError(f"Invalid dataset line {line_number}: {error}") from error

            records.append(
                {
                    "line_number": line_number,
                    "record": record,
                    "raw": raw,
                    "message": message,
                    "text": get_message_text(message),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
    return records


def feature_text(example):
    """Build a deliberately simple subject/sender/body text feature string."""
    message = example["message"]
    sender = message.get("From", "")
    subject = message.get("Subject", "")
    return f"{subject}\n{sender}\n{example['text']}"


def tokenize(text):
    return TOKEN_RE.findall(text.casefold())


class MultinomialNaiveBayes:
    """Small educational multinomial Naive Bayes implementation."""

    def fit(self, texts, labels):
        if not texts or len(texts) != len(labels):
            raise ValueError("Training texts and labels must be non-empty and aligned.")
        if set(labels) != set(LABELS):
            raise ValueError("The demo model needs at least one example of each label.")

        self.class_counts = Counter(labels)
        self.word_counts = {label: Counter() for label in LABELS}
        self.total_tokens = Counter()
        self.vocabulary = set()

        for text, label in zip(texts, labels):
            tokens = tokenize(text)
            self.word_counts[label].update(tokens)
            self.total_tokens[label] += len(tokens)
            self.vocabulary.update(tokens)

        if not self.vocabulary:
            raise ValueError("No usable text tokens were found in the messages.")
        return self

    def predict_proba(self, text):
        tokens = tokenize(text)
        vocabulary_size = len(self.vocabulary)
        total_examples = sum(self.class_counts.values())
        scores = {}
        for label in LABELS:
            score = math.log(self.class_counts[label] / total_examples)
            denominator = self.total_tokens[label] + vocabulary_size
            for token in tokens:
                score += math.log(
                    (self.word_counts[label][token] + 1) / denominator
                )
            scores[label] = score

        max_score = max(scores.values())
        exponentials = {
            label: math.exp(score - max_score) for label, score in scores.items()
        }
        total = sum(exponentials.values())
        return {label: value / total for label, value in exponentials.items()}

    def top_tokens(self, label, count=8):
        vocabulary_size = len(self.vocabulary)
        denominator = self.total_tokens[label] + vocabulary_size
        return sorted(
            self.vocabulary,
            key=lambda token: (
                self.word_counts[label][token] + 1
            ) / denominator,
            reverse=True,
        )[:count]


def print_examples(records, show_content):
    for index, example in enumerate(records, start=1):
        record = example["record"]
        message = example["message"]
        attachments = [
            part.get_filename()
            for part in message.walk()
            if part.get_content_disposition() == "attachment"
        ]

        print(f"\n{'=' * 78}")
        print(
            f"Example {index} | source line {example['line_number']} | "
            f"label: {record['classification']}"
        )
        print(f"Recorded at: {record.get('recorded_at', '(not provided)')}")
        print(f"Mailbox: {record.get('mailbox', '(not provided)')}")
        print(f"Message ID: {record.get('message_id', '(not provided)')}")
        print(f"Raw RFC822 bytes: {len(example['raw']):,}")
        print(f"SHA-256: {example['sha256']}")
        print(f"From: {message.get('From', '')}")
        print(f"To: {message.get('To', '')}")
        print(f"Cc: {message.get('Cc', '')}")
        print(f"Date: {message.get('Date', '')}")
        print(f"Subject: {message.get('Subject', '')}")
        print(f"MIME types: {', '.join(sorted({part.get_content_type() for part in message.walk()}))}")
        print(f"Attachments: {len(attachments)}")
        for attachment_name in attachments:
            print(f"  - {attachment_name or '(unnamed attachment)'}")
        print(f"Extracted text characters: {len(example['text']):,}")
        if show_content:
            print("\nExtracted body text:")
            print(example["text"] or "(no readable text parts)")
        else:
            preview = " ".join(example["text"].split())
            if len(preview) > 500:
                preview = preview[:500] + "..."
            print(f"Body preview: {preview or '(no readable text parts)'}")
        print("Headers:")
        for name, value in message.items():
            print(f"  {name}: {value}")


def print_model_demo(records):
    labels = [example["record"]["classification"] for example in records]
    counts = Counter(labels)
    fingerprints = defaultdict(set)
    for example in records:
        fingerprints[example["sha256"]].add(example["record"]["classification"])
    conflicts = sum(len(group_labels) > 1 for group_labels in fingerprints.values())

    print("\n\n" + "=" * 78)
    print("DATASET SUMMARY")
    print(f"Valid examples: {len(records)}")
    print(f"Labels: important={counts['important']}, not_important={counts['not_important']}")
    print(f"Exact unique messages: {len(fingerprints)}")
    print(f"Exact-message groups with conflicting labels: {conflicts}")

    if len(counts) < 2:
        print("\nML demo skipped: both labels are needed to fit a binary classifier.")
        return

    texts = [feature_text(example) for example in records]
    model = MultinomialNaiveBayes().fit(texts, labels)
    print("\nMODEL DEMONSTRATION")
    print("Algorithm: multinomial Naive Bayes with Laplace smoothing (standard library)")
    print("Features: tokens from Subject + From + extracted text body")
    print(f"Vocabulary size: {len(model.vocabulary)}")
    print("Predictions below use the same examples used for fitting.")
    print("They demonstrate the data-to-model pipeline; they are NOT test accuracy.")
    print("\nLearned frequent tokens by class (may contain private email terms):")
    for label in LABELS:
        print(f"  {label}: {', '.join(model.top_tokens(label))}")

    print("\nTraining-set predictions:")
    for index, (example, text) in enumerate(zip(records, texts), start=1):
        probabilities = model.predict_proba(text)
        prediction = max(probabilities, key=probabilities.get)
        confidence = probabilities[prediction] * 100
        actual = example["record"]["classification"]
        print(
            f"  Example {index}: predicted={prediction} ({confidence:.1f}%), "
            f"actual={actual}, "
            f"{'match' if prediction == actual else 'mismatch'}"
        )

    if len(records) < 30 or min(counts[label] for label in LABELS) < 10:
        print(
            "\nCaution: this dataset is too small for a trustworthy quality estimate. "
            "Collect more varied labels, then evaluate on held-out messages grouped "
            "by duplicate/thread and preferably by time."
        )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Decode and inspect the manual email dataset, then fit an educational "
            "local Naive Bayes classifier."
        )
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(__file__).with_name("manual_classification.jsonl"),
        help="JSONL dataset path (defaults to this directory's app dataset).",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show a short body preview instead of the full extracted message text.",
    )
    args = parser.parse_args()

    if not args.data.is_file():
        parser.error(f"Dataset file not found: {args.data}")

    try:
        records = load_records(args.data)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    if not records:
        print(f"No labeled examples found in {args.data}")
        return 0

    print(f"Dataset: {args.data.resolve()}")
    print(
        "Privacy note: parsed headers and body text can contain sensitive "
        "information; full bodies are shown unless --summary is used."
    )
    print_examples(records, show_content=not args.summary)
    print_model_demo(records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
