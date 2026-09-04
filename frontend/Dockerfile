FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --legacy-peer-deps

COPY . .
RUN npx ng build --configuration=production

FROM nginx:alpine

COPY --from=build /app/dist/naragate/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 4273

CMD ["nginx", "-g", "daemon off;"]
