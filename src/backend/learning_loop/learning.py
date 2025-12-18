from google.cloud import firestore


class LearningLoop:
    def __init__(self, db):
        self.db = db

    def save_learning_example(
        self, doc_type: str, field_name: str, ai_value: str, human_value: str
    ):
        if ai_value == human_value:
            return

        self.db.collection("learning_examples").add(
            {
                "doc_type": doc_type,
                "field": field_name,
                "bad_example": ai_value,
                "good_example": human_value,
                "timestamp": firestore.SERVER_TIMESTAMP,
            }
        )

    def get_learning_context(self, doc_type: str) -> str:
        docs = (
            self.db.collection("learning_examples")
            .where("doc_type", "==", doc_type)
            .order_by("timestamp", direction="DESCENDING")
            .limit(3)
            .stream()
        )

        examples_text = ""
        for doc in docs:
            data = doc.to_dict()
            examples_text += f"- FORMATTING RULE for '{data['field']}': previously, the user corrected the format '{data['bad_example']}' to '{data['good_example']}'. Ensure you apply a similar FORMAT pattern (e.g. hyphens, spacing) to the data you see now, but DO NOT copy the values.\n"

        return examples_text
