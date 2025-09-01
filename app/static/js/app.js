name: CI (build → test → docker → notify dashboard)

on:
  push:
    branches: ["main"]
  workflow_dispatch:

jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set git meta outputs
        id: meta
        run: |
          echo "branch=${GITHUB_REF_NAME}" >> $GITHUB_OUTPUT
          echo "commit=$(git rev-parse --short HEAD)" >> $GITHUB_OUTPUT
          echo "author=$(git log -1 --pretty=format:'%an')" >> $GITHUB_OUTPUT
          echo "date=$(git log -1 --date=format:'%Y-%m-%d %H:%M:%S' --pretty=format:'%ad')" >> $GITHUB_OUTPUT

      - name: Notify dashboard: Build started
        run: |
          curl -sS -X POST "${{ secrets.DASHBOARD_URL }}/api/ci/update" \
            -H "Content-Type: application/json" \
            -H "X-CI-TOKEN: ${{ secrets.CI_UPDATE_TOKEN }}" \
            -d "{\"build\":\"Running\",\"test\":\"Pending\",\"deploy\":\"Pending\", \
                 \"branch\":\"${{ steps.meta.outputs.branch }}\", \
                 \"commit\":\"${{ steps.meta.outputs.commit }}\", \
                 \"author\":\"${{ steps.meta.outputs.author }}\", \
                 \"date\":\"${{ steps.meta.outputs.date }}\" }"
      - name: Install Python
        uses: actions/setup-python@v5
        with: { python-version: "3.12" }

      - name: Install deps
        run: pip install -r requirements.txt

      - name: Run tests
        run: |
          set -e
          echo "Running tests..."
          # put your tests here, e.g.:
          # pytest -q
          echo "No tests yet - treating as success"

      - name: Notify dashboard: Build/Test succeeded
        if: success()
        run: |
          curl -sS -X POST "${{ secrets.DASHBOARD_URL }}/api/ci/update" \
            -H "Content-Type: application/json" \
            -H "X-CI-TOKEN: ${{ secrets.CI_UPDATE_TOKEN }}" \
            -d "{\"build\":\"Succeeded\",\"test\":\"Succeeded\"}"

      - name: Docker login
        run: echo "${{ secrets.DOCKERHUB_TOKEN }}" | docker login -u "${{ secrets.DOCKERHUB_USERNAME }}" --password-stdin

      - name: Build Docker image
        run: |
          docker build -t ${{ secrets.DOCKERHUB_USERNAME }}/ci-cd-dashboard:${{ steps.meta.outputs.commit }} \
                       -t ${{ secrets.DOCKERHUB_USERNAME }}/ci-cd-dashboard:latest .

      - name: Push Docker image
        run: |
          docker push ${{ secrets.DOCKERHUB_USERNAME }}/ci-cd-dashboard:${{ steps.meta.outputs.commit }}
          docker push ${{ secrets.DOCKERHUB_USERNAME }}/ci-cd-dashboard:latest

      - name: Notify dashboard: Deploy running
        run: |
          curl -sS -X POST "${{ secrets.DASHBOARD_URL }}/api/ci/update" \
            -H "Content-Type: application/json" \
            -H "X-CI-TOKEN: ${{ secrets.CI_UPDATE_TOKEN }}" \
            -d "{\"deploy\":\"Running\"}"

  # Optional: separate job to ping "deploy succeeded"
  finalize:
    needs: build-test
    runs-on: ubuntu-latest
    steps:
      - name: Notify dashboard: Deploy succeeded
        run: |
          curl -sS -X POST "${{ secrets.DASHBOARD_URL }}/api/ci/update" \
            -H "Content-Type: application/json" \
            -H "X-CI-TOKEN: ${{ secrets.CI_UPDATE_TOKEN }}" \
            -d "{\"deploy\":\"Succeeded\"}"
