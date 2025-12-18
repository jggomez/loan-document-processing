#!/bin/bash
set -e

PROJECT_ID="devhack-3f0c2"

SERVICE_ACCOUNT="agents@${PROJECT_ID}.iam.gserviceaccount.com"

SERVICE_NAME="load-document-processing"

REGION="us-central1"

IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "Building agent Docker image: ${IMAGE_NAME}"
gcloud builds submit --tag "${IMAGE_NAME}" . --project "${PROJECT_ID}"

echo "Deploying agent to Cloud Run service: ${SERVICE_NAME}"
gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE_NAME}" \
    --service-account "${SERVICE_ACCOUNT}" \
    --update-secrets API_KEY=GOOGLE_GENAI_API_KEY:latest \
    --update-env-vars=PROJECT_ID=${PROJECT_ID} \
    --update-env-vars=BUCKET_NAME=questionsanswersproject \
    --platform "managed" \
    --region "${REGION}" \
    --allow-unauthenticated \
    --project "${PROJECT_ID}"

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --platform "managed" --region "${REGION}" --project "${PROJECT_ID}" --format="value(status.url)")

echo -e "\Service deployment successful!"
echo "Your service is available at: ${SERVICE_URL}"
