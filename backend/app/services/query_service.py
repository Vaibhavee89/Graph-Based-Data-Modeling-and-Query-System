"""Query service - Natural language query processing."""
import re
import networkx as nx
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.llm_service import LLMService
from app.services.guardrail_service import GuardrailService
from app.schemas.query import QueryResponse, IntentClassification


class QueryService:
    """Service for processing natural language queries."""

    def __init__(self, db: Session, graph: nx.DiGraph):
        """
        Initialize query service.

        Args:
            db: Database session
            graph: NetworkX graph
        """
        self.db = db
        self.graph = graph
        self.llm = LLMService()
        self.guardrail = GuardrailService()

    def process_query(self, query: str) -> QueryResponse:
        """
        Process a natural language query.

        Args:
            query: User's natural language query

        Returns:
            QueryResponse with answer and data
        """
        print(f"\n{'='*60}")
        print(f"Processing query: {query}")
        print(f"{'='*60}")

        # Step 1: Validate query is domain-related
        validation = self.guardrail.validate_query(query)
        print(f"Validation: {validation.is_valid} - {validation.reason}")

        if not validation.is_valid:
            return QueryResponse(
                success=False,
                message=f"Query rejected: {validation.reason}",
                answer="I can only answer questions about business data (customers, orders, products, invoices, payments, deliveries). Please ask a question related to this domain."
            )

        # Handle greetings
        if validation.reason == "Greeting or acknowledgment":
            return QueryResponse(
                success=True,
                answer="Hello! I'm here to help you analyze your business data. You can ask me questions about customers, orders, products, invoices, payments, and deliveries. What would you like to know?"
            )

        try:
            # Step 2: Classify intent
            intent = self._classify_intent(query)
            print(f"Intent: {intent.intent} (confidence: {intent.confidence})")

            # Step 3: Execute query based on intent
            if intent.intent == "ENTITY_LOOKUP":
                result = self._handle_entity_lookup(query)
            elif intent.intent == "AGGREGATION":
                result = self._handle_aggregation(query)
            elif intent.intent == "TRAVERSAL":
                result = self._handle_traversal(query)
            elif intent.intent == "ANOMALY_DETECTION":
                result = self._handle_anomaly_detection(query)
            else:
                result = self._handle_general(query)

            # Step 4: Format response
            return result

        except Exception as e:
            print(f"Query processing error: {e}")
            import traceback
            traceback.print_exc()

            return QueryResponse(
                success=False,
                message=f"Error processing query: {str(e)}",
                answer="I encountered an error processing your query. Please try rephrasing your question."
            )

    def _classify_intent(self, query: str) -> IntentClassification:
        """Classify the intent of the query."""
        system_prompt = """You are an intent classifier for business data queries.

Classify queries into one of these intents:
- AGGREGATION: Counting, summing, finding highest/lowest, statistics
- TRAVERSAL: Tracing flows, finding paths, exploring relationships
- ANOMALY_DETECTION: Finding broken/incomplete flows, data quality issues
- ENTITY_LOOKUP: Finding specific entities by name/ID/properties"""

        prompt = f"""Query: "{query}"

Classify this query's intent.

Examples:
- "Which products have most orders?" → AGGREGATION
- "Trace the flow of invoice INV-123" → TRAVERSAL
- "Find orders with missing invoices" → ANOMALY_DETECTION
- "Show me customer 310000108" → ENTITY_LOOKUP

Return JSON:
{{
    "intent": "AGGREGATION|TRAVERSAL|ANOMALY_DETECTION|ENTITY_LOOKUP",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation"
}}"""

        try:
            result = self.llm.generate_structured(prompt, system_prompt)
            return IntentClassification(**result)
        except Exception as e:
            print(f"Intent classification error: {e}")
            return IntentClassification(
                intent="AGGREGATION",
                confidence=0.5,
                reasoning="Fallback due to error"
            )

    def _handle_entity_lookup(self, query: str) -> QueryResponse:
        """Handle entity lookup queries."""
        # Extract entity IDs from query
        entity_pattern = r'\b([A-Z]+-\d+)\b|\b(\d{9})\b'
        matches = re.findall(entity_pattern, query)
        entity_ids = [m[0] or m[1] for m in matches]

        if entity_ids:
            # Look up entities in graph
            found_entities = []
            for entity_id in entity_ids:
                if self.graph.has_node(entity_id):
                    node_data = self.graph.nodes[entity_id]
                    found_entities.append({
                        'id': entity_id,
                        'type': node_data.get('type'),
                        'label': node_data.get('label'),
                        'properties': node_data.get('properties', {})
                    })

            if found_entities:
                # Format response
                entity_descriptions = []
                for entity in found_entities:
                    entity_descriptions.append(
                        f"**{entity['type']} {entity['id']}**: {entity['label']}"
                    )

                answer = "I found the following entities:\n\n" + "\n".join(entity_descriptions)

                return QueryResponse(
                    success=True,
                    answer=answer,
                    data=found_entities,
                    entities=entity_ids,
                    intent="ENTITY_LOOKUP"
                )

        return QueryResponse(
            success=False,
            message="No entities found",
            answer="I couldn't find any entities matching your query. Please provide a valid entity ID (e.g., CUST-0001, ORD-0123)."
        )

    def _handle_aggregation(self, query: str) -> QueryResponse:
        """Handle aggregation queries using SQL."""
        print("Handling aggregation query...")

        # Get database schema
        schema = self._get_database_schema()

        # Generate SQL query
        system_prompt = """You are a SQL query generator for a business database.

Generate SAFE, READ-ONLY PostgreSQL queries. Use proper JOINs and aggregations.

IMPORTANT:
- Only SELECT queries (no INSERT, UPDATE, DELETE, DROP)
- Use proper table names and column names from the schema
- Include ORDER BY and LIMIT for results
- Handle NULL values appropriately"""

        sql_prompt = f"""Database schema:
{schema}

User query: "{query}"

Generate a PostgreSQL SELECT query to answer this question.

Return JSON:
{{
    "sql": "SELECT ... FROM ... WHERE ... ORDER BY ... LIMIT ...",
    "explanation": "What the query does"
}}"""

        try:
            result = self.llm.generate_structured(sql_prompt, system_prompt)
            sql = result.get('sql', '')
            explanation = result.get('explanation', '')

            print(f"Generated SQL: {sql}")
            print(f"Explanation: {explanation}")

            # Validate SQL (basic safety check)
            if not self._is_safe_sql(sql):
                raise Exception("Generated SQL failed safety validation")

            # Execute SQL
            query_result = self.db.execute(text(sql))
            rows = query_result.fetchall()

            # Format results
            data = [dict(row._mapping) for row in rows]

            # Generate natural language answer
            answer = self._format_aggregation_answer(query, data, explanation)

            return QueryResponse(
                success=True,
                answer=answer,
                data=data,
                intent="AGGREGATION"
            )

        except Exception as e:
            print(f"Aggregation error: {e}")
            return QueryResponse(
                success=False,
                message=str(e),
                answer="I encountered an error executing your query. Please try rephrasing."
            )

    def _handle_traversal(self, query: str) -> QueryResponse:
        """Handle graph traversal queries."""
        print("Handling traversal query...")

        # Extract entity IDs
        entity_pattern = r'\b([A-Z]+-\d+)\b|\b(\d{9})\b'
        matches = re.findall(entity_pattern, query)
        entity_ids = [m[0] or m[1] for m in matches]

        if not entity_ids:
            return QueryResponse(
                success=False,
                message="No entity ID found in query",
                answer="Please provide an entity ID to trace (e.g., 'Trace invoice INV-0001')."
            )

        entity_id = entity_ids[0]

        if not self.graph.has_node(entity_id):
            return QueryResponse(
                success=False,
                message="Entity not found in graph",
                answer=f"I couldn't find entity {entity_id} in the graph."
            )

        # Perform traversal
        node_data = self.graph.nodes[entity_id]
        node_type = node_data.get('type')

        # Build flow path based on entity type
        flow = self._trace_flow(entity_id, node_type)

        # Format answer
        answer = self._format_traversal_answer(entity_id, flow)

        return QueryResponse(
            success=True,
            answer=answer,
            data=flow,
            entities=list(flow.keys()),
            intent="TRAVERSAL"
        )

    def _handle_anomaly_detection(self, query: str) -> QueryResponse:
        """Handle anomaly detection queries."""
        print("Handling anomaly detection query...")

        # Find orders without invoices or deliveries
        anomalies = {
            'orders_without_invoices': [],
            'orders_without_deliveries': [],
            'invoices_without_payments': [],
        }

        # Check orders
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('type') == 'Order':
                # Check for invoice
                has_invoice = False
                has_delivery = False

                for successor in self.graph.successors(node_id):
                    succ_type = self.graph.nodes[successor].get('type')
                    if succ_type == 'Invoice':
                        has_invoice = True
                    elif succ_type == 'Delivery':
                        has_delivery = True

                if not has_invoice:
                    anomalies['orders_without_invoices'].append(node_id)
                if not has_delivery:
                    anomalies['orders_without_deliveries'].append(node_id)

            elif node_data.get('type') == 'Invoice':
                # Check for payment
                has_payment = any(
                    self.graph.nodes[s].get('type') == 'Payment'
                    for s in self.graph.successors(node_id)
                )
                if not has_payment:
                    anomalies['invoices_without_payments'].append(node_id)

        # Format answer
        answer = self._format_anomaly_answer(anomalies)

        return QueryResponse(
            success=True,
            answer=answer,
            data=anomalies,
            intent="ANOMALY_DETECTION"
        )

    def _handle_general(self, query: str) -> QueryResponse:
        """Handle general queries."""
        # Use LLM to provide a general answer about the data
        system_prompt = f"""You are a helpful assistant for a business data analysis system.

The system contains data about customers, products, orders, invoices, payments, and deliveries.

Current data statistics:
- Total nodes: {self.graph.number_of_nodes()}
- Total edges: {self.graph.number_of_edges()}

Provide helpful, accurate answers based on this context."""

        try:
            answer = self.llm.generate_completion(query, system_prompt)
            return QueryResponse(
                success=True,
                answer=answer
            )
        except Exception as e:
            return QueryResponse(
                success=False,
                message=str(e),
                answer="I encountered an error. Please try rephrasing your question."
            )

    def _trace_flow(self, entity_id: str, entity_type: str) -> Dict[str, Any]:
        """Trace the flow for an entity."""
        flow = {'start': entity_id, 'type': entity_type}

        if entity_type == 'Order':
            # Order → Invoice → Payment
            # Order → Delivery → Address
            for successor in self.graph.successors(entity_id):
                succ_type = self.graph.nodes[successor].get('type')
                succ_label = self.graph.nodes[successor].get('label')

                if succ_type == 'Invoice':
                    flow['invoice'] = {'id': successor, 'label': succ_label}
                    # Check for payment
                    for payment in self.graph.successors(successor):
                        if self.graph.nodes[payment].get('type') == 'Payment':
                            flow['payment'] = {
                                'id': payment,
                                'label': self.graph.nodes[payment].get('label')
                            }
                            break

                elif succ_type == 'Delivery':
                    flow['delivery'] = {'id': successor, 'label': succ_label}

                elif succ_type == 'Product':
                    if 'products' not in flow:
                        flow['products'] = []
                    flow['products'].append({'id': successor, 'label': succ_label})

        elif entity_type == 'Invoice':
            # Invoice → Payment
            # Invoice ← Order
            for successor in self.graph.successors(entity_id):
                if self.graph.nodes[successor].get('type') == 'Payment':
                    flow['payment'] = {
                        'id': successor,
                        'label': self.graph.nodes[successor].get('label')
                    }

            for predecessor in self.graph.predecessors(entity_id):
                if self.graph.nodes[predecessor].get('type') == 'Order':
                    flow['order'] = {
                        'id': predecessor,
                        'label': self.graph.nodes[predecessor].get('label')
                    }

        return flow

    def _format_traversal_answer(self, entity_id: str, flow: Dict) -> str:
        """Format traversal results as natural language."""
        lines = [f"**Flow trace for {entity_id}:**\n"]

        entity_type = flow.get('type')

        if entity_type == 'Order':
            lines.append(f"📋 **Order**: {entity_id}")

            if 'products' in flow:
                lines.append(f"  ↓ contains")
                for prod in flow['products'][:5]:  # Limit to 5
                    lines.append(f"  📦 **Product**: {prod['label']}")

            if 'invoice' in flow:
                inv = flow['invoice']
                lines.append(f"  ↓ generated")
                lines.append(f"  📄 **Invoice**: {inv['id']}")

                if 'payment' in flow:
                    pay = flow['payment']
                    lines.append(f"    ↓ paid by")
                    lines.append(f"    💳 **Payment**: {pay['id']}")

            if 'delivery' in flow:
                deliv = flow['delivery']
                lines.append(f"  ↓ resulted in")
                lines.append(f"  🚚 **Delivery**: {deliv['id']}")

            # Check completeness
            has_invoice = 'invoice' in flow
            has_payment = 'payment' in flow
            has_delivery = 'delivery' in flow

            lines.append(f"\n**Flow Status**: {'✅ Complete' if (has_invoice and has_payment and has_delivery) else '⚠️ Incomplete'}")

        elif entity_type == 'Invoice':
            lines.append(f"📄 **Invoice**: {entity_id}")

            if 'order' in flow:
                lines.append(f"  ← generated from")
                lines.append(f"  📋 **Order**: {flow['order']['id']}")

            if 'payment' in flow:
                lines.append(f"  ↓ paid by")
                lines.append(f"  💳 **Payment**: {flow['payment']['id']}")

        return "\n".join(lines)

    def _format_aggregation_answer(self, query: str, data: List[Dict], explanation: str) -> str:
        """Format aggregation results."""
        if not data:
            return "No results found for your query."

        # Create answer with explanation and data
        lines = [explanation, "\n**Results:**\n"]

        # Show first 10 results
        for i, row in enumerate(data[:10], 1):
            row_str = ", ".join(f"{k}: {v}" for k, v in row.items())
            lines.append(f"{i}. {row_str}")

        if len(data) > 10:
            lines.append(f"\n... and {len(data) - 10} more results")

        return "\n".join(lines)

    def _format_anomaly_answer(self, anomalies: Dict) -> str:
        """Format anomaly detection results."""
        lines = ["**Anomaly Detection Results:**\n"]

        total = sum(len(v) for v in anomalies.values())

        if total == 0:
            return "✅ No anomalies found! All orders have complete flows."

        lines.append(f"Found **{total}** potential issues:\n")

        if anomalies['orders_without_invoices']:
            count = len(anomalies['orders_without_invoices'])
            lines.append(f"📋 **{count} orders without invoices**")
            for order_id in anomalies['orders_without_invoices'][:5]:
                lines.append(f"  - {order_id}")
            if count > 5:
                lines.append(f"  ... and {count - 5} more")
            lines.append("")

        if anomalies['orders_without_deliveries']:
            count = len(anomalies['orders_without_deliveries'])
            lines.append(f"🚚 **{count} orders without deliveries**")
            for order_id in anomalies['orders_without_deliveries'][:5]:
                lines.append(f"  - {order_id}")
            if count > 5:
                lines.append(f"  ... and {count - 5} more")
            lines.append("")

        if anomalies['invoices_without_payments']:
            count = len(anomalies['invoices_without_payments'])
            lines.append(f"💳 **{count} invoices without payments**")
            for inv_id in anomalies['invoices_without_payments'][:5]:
                lines.append(f"  - {inv_id}")
            if count > 5:
                lines.append(f"  ... and {count - 5} more")

        return "\n".join(lines)

    def _get_database_schema(self) -> str:
        """Get database schema description."""
        return """
Tables:
- customers (customer_id, name, email, segment)
- products (product_id, name, category, price)
- orders (order_id, customer_id, order_date, status, total_amount)
- order_items (id, order_id, product_id, quantity, unit_price, subtotal)
- invoices (invoice_id, order_id, invoice_date, due_date, amount, status)
- payments (payment_id, invoice_id, payment_date, amount, method, status)
- deliveries (delivery_id, order_id, address_id, delivery_date, status, tracking_number)
- addresses (address_id, customer_id, street, city, state, country, address_type)
"""

    def _is_safe_sql(self, sql: str) -> bool:
        """Validate SQL is safe (read-only)."""
        sql_upper = sql.upper().strip()

        # Must start with SELECT
        if not sql_upper.startswith('SELECT'):
            return False

        # Disallow dangerous keywords
        dangerous = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE']
        for keyword in dangerous:
            if keyword in sql_upper:
                return False

        return True
