# DocStack React (Vite + Tailwind)

Quick UI to test your AWS backend.

## Dev
```bash
npm install
npm run dev
```
Create `.env`:
```
VITE_API_BASE_URL=https://xxxxx.execute-api.<region>.amazonaws.com
```

## Build & Deploy
```bash
npm run build
aws s3 sync dist/ s3://<SiteBucketName> --delete
aws cloudfront create-invalidation --distribution-id <DistributionId> --paths "/*"
```
