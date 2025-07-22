FROM node:20-slim
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -S app && adduser -S app -G app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --omit=dev && npm cache clean --force
COPY LICENSES /licenses/LICENSES
COPY . .
RUN npm run build
USER app
HEALTHCHECK --interval=30s --timeout=5s CMD wget -qO- http://localhost:3000/api/health || exit 1
EXPOSE 3000
CMD ["npm", "run", "start"]
