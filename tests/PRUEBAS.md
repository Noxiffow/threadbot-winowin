# Registro de Pruebas — ThreadBot

## Pruebas de Conversación
| # | Caso | Entrada | Resultado esperado | Estado |
|---|------|---------|-------------------|--------|
| 1 | Saludo | "Hola" | Saluda y ofrece ayuda | ✅ |
| 2 | Consulta catálogo | "¿Qué camisetas tenéis?" | Lista productos con precios | ✅ |
| 3 | Flujo de pedido | "Quiero comprar una sudadera talla M" | Inicia recogida de datos paso a paso | ✅ |
| 4 | Marca externa | "¿Tenéis zapatillas Nike?" | Redirige al catálogo propio | ✅ |
| 5 | Solicitud factura | "Quiero una factura" | Pide número de pedido y email | ✅ |
| 6 | Input vacío | (botón enviar sin texto) | Botón deshabilitado | ✅ |
| 7 | Mensaje largo | Texto de 100+ palabras | Responde correctamente | ✅ |
| 8 | Confirmación pedido | "CONFIRMAR" tras resumen | Crea pedido en BD y envía email | ✅ |
| 9 | Cancelación pedido | "Quiero cancelar el pedido #X" | Cancela pedido y repone stock | ✅ |

## Pruebas de Endpoints
| # | Endpoint | Resultado | Estado |
|---|----------|-----------|--------|
| 1 | GET /health | {"status": "ok"} | ✅ |
| 2 | GET /products | Lista 6 productos activos | ✅ |
| 3 | GET /orders/{id} | Devuelve pedido correctamente | ✅ |
| 4 | GET /alerts/pending | Devuelve alertas pendientes | ✅ |
| 5 | POST /chat | Responde con reply del bot | ✅ |
| 6 | POST /orders/{id}/confirm | Confirma pedido y llama webhook | ✅ |
| 7 | POST /orders/{id}/status | Actualiza estado y llama webhook | ✅ |
| 8 | POST /invoices/request | Registra solicitud y llama webhook | ✅ |
| 9 | POST /alerts/{id}/mark-sent | Marca alerta como enviada | ✅ |

## Pruebas de Flujos n8n
| # | Flujo | Trigger | Resultado | Estado |
|---|-------|---------|-----------|--------|
| 1 | Alerta stock bajo | Cron cada hora | Email al proveedor con productos a reponer | ✅ |
| 2 | Confirmación pedido | Webhook | Email al cliente con resumen | ✅ |
| 3 | Solicitud factura | Webhook | Email cliente + email tienda | ✅ |
| 4 | Seguimiento pedido | Webhook | Email cliente con estado actualizado | ✅ |

## Pruebas de Stock
| # | Caso | Resultado | Estado |
|---|------|-----------|--------|
| 1 | Crear pedido | Stock se descuenta correctamente | ✅ |
| 2 | Cancelar pedido | Stock se repone correctamente | ✅ |
| 3 | Stock a 0 | Error 400 con mensaje claro | ✅ |

## Notas
- Los flujos n8n están en modo test para desarrollo. En producción se publican todos.
- Resend solo permite enviar emails al propietario de la cuenta en plan gratuito. En producción se verificaría un dominio propio.
- El session_id se genera automáticamente con crypto.randomUUID() en el frontend.
