FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
ARG VITE_PRODUCT_API=/api/products
ARG VITE_ORDER_API=/api/orders
ARG VITE_AI_API=/api/ai
ENV VITE_PRODUCT_API=$VITE_PRODUCT_API VITE_ORDER_API=$VITE_ORDER_API VITE_AI_API=$VITE_AI_API
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
