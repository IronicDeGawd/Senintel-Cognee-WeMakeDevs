# Multi-stage Next.js standalone build for Cloud Run.
# Build args: NEXT_PUBLIC_API_BASE is baked into the client bundle at build time
# (NEXT_PUBLIC_* env is read at compile time, not at container start).

FROM node:24-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev=false

FROM node:24-alpine AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_BASE=""
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:24-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=8080
ENV HOSTNAME=0.0.0.0
# Cloud Run sets PORT; default 8080 for local docker runs.

# next standalone packs the trimmed server + a node_modules subset.
# public/ and .next/static/ are not auto-copied — pull them in by hand.
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 8080
CMD ["node", "server.js"]
