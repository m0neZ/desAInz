# Admin Dashboard tRPC Integration

The admin dashboard communicates with backend services exclusively through the API Gateway using **tRPC**. This approach provides full type-safety across the client and server, ensuring that requests and responses adhere to the same contract.

When a user interacts with the dashboard, the frontend issues tRPC calls to the API Gateway. The gateway then routes these requests to the appropriate microservice. Authentication tokens are forwarded automatically, so each downstream service can validate permissions without additional logic in the dashboard.

All tRPC routes are declared in the `api-gateway` package. The dashboard imports the generated TypeScript types to guarantee that its calls match the server's expectations. Errors are propagated back through the gateway and surfaced in the dashboard's UI.

For more details on implementing new routes, see the `api-gateway` documentation and the tRPC project guidelines.

## Tailwind Configuration

The dashboard uses a custom Tailwind setup defined in `tailwind.config.ts`. The theme
extends the default palette with a `brand` color and sets the sans and mono font
families from CSS variables. This ensures consistent colors and fonts across all
components.

