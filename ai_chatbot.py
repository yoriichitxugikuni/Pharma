import streamlit as st
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

# Check if OpenAI is available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

class PharmaceuticalChatbot:
    def __init__(self, db):
        self.db = db
        self.openai_client = None
        if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY"):
            self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
        # Initialize conversation history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
            
        # Predefined responses for common queries when OpenAI is not available
        self.fallback_responses = {
            "inventory": "I can help you check current inventory levels, low stock items, and expiring drugs.",
            "drug_info": "I can provide basic information about drugs in your inventory including dosage, category, and supplier details.",
            "interactions": "I can check for potential drug interactions using our built-in interaction database.",
            "ordering": "I can suggest items to reorder based on consumption patterns and current stock levels.",
            "expiry": "I can show you items nearing expiry and suggest actions to prevent wastage.",
            "analytics": "I can provide insights from your inventory data including trends and forecasts."
        }
    
    def get_system_context(self) -> str:
        """Get current system context for the AI"""
        try:
            # Get current inventory stats
            inventory_df = self.db.get_inventory()
            total_items = len(inventory_df)
            low_stock_items = len(inventory_df[inventory_df['current_stock'] < inventory_df['min_stock_level']])
            
            # Get expiring items
            expiring_items = self.db.get_expiring_drugs(days_ahead=30)
            
            # Get recent transactions
            recent_transactions = self.db.get_recent_transactions(limit=5)
            
            context = f"""
You are an AI assistant for a pharmaceutical inventory management system. Here's the current system status:

INVENTORY OVERVIEW:
- Total items in inventory: {total_items}
- Items with low stock: {low_stock_items}
- Items expiring in next 30 days: {len(expiring_items)}

RECENT ACTIVITY:
- Last {len(recent_transactions)} transactions recorded

You can help users with:
1. Inventory queries (stock levels, item details, categories)
2. Drug information and interactions
3. Reordering suggestions and supplier information
4. Expiry management and wastage prevention
5. Analytics and insights from inventory data
6. General pharmaceutical knowledge

Always provide accurate, helpful responses focused on pharmaceutical inventory management.
"""
            return context
        except Exception as e:
            return "You are an AI assistant for a pharmaceutical inventory management system."
    
    def query_inventory_data(self, query: str) -> Dict:
        """Query the database for relevant information based on user query"""
        try:
            results = {}
            query_lower = query.lower()
            
            # Check if query is about specific drug
            if any(word in query_lower for word in ['drug', 'medicine', 'medication', 'tablet', 'capsule']):
                inventory_df = self.db.get_inventory()
                # Simple keyword search in drug names
                words = query_lower.split()
                drug_matches = []
                for _, drug in inventory_df.iterrows():
                    drug_name_lower = drug['drug_name'].lower()
                    if any(word in drug_name_lower for word in words):
                        drug_matches.append(drug.to_dict())
                
                if drug_matches:
                    results['matching_drugs'] = drug_matches[:5]  # Limit to 5 matches
            
            # Check if query is about stock levels
            if any(word in query_lower for word in ['stock', 'level', 'quantity', 'low', 'empty']):
                inventory_df = self.db.get_inventory()
                low_stock = inventory_df[inventory_df['current_stock'] < inventory_df['min_stock_level']]
                results['low_stock_items'] = low_stock.to_dict('records')[:10]
            
            # Check if query is about expiry
            if any(word in query_lower for word in ['expiry', 'expire', 'expiring', 'expired']):
                expiring_items = self.db.get_expiring_drugs(days_ahead=30)
                results['expiring_items'] = expiring_items[:10]
            
            # Check if query is about transactions
            if any(word in query_lower for word in ['transaction', 'sale', 'purchase', 'recent']):
                recent_transactions = self.db.get_recent_transactions(limit=10)
                results['recent_transactions'] = recent_transactions.to_dict('records')
            
            return results
        except Exception as e:
            return {'error': str(e)}
    
    def generate_ai_response(self, user_message: str) -> str:
        """Generate AI response using OpenAI or fallback responses"""
        if not self.openai_client:
            return self.generate_fallback_response(user_message)
        
        try:
            # Get current system context
            system_context = self.get_system_context()
            
            # Query relevant data
            data_context = self.query_inventory_data(user_message)
            
            # Prepare context for AI
            context_message = f"{system_context}\n\nRELEVANT DATA:\n{json.dumps(data_context, indent=2, default=str)}"
            
            # Create messages for OpenAI
            messages = [
                {"role": "system", "content": context_message},
                {"role": "user", "content": user_message}
            ]
            
            # Add recent conversation history for context (last 3 exchanges)
            recent_history = st.session_state.chat_history[-6:]
            for msg in recent_history:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": str(msg["content"])
                    })
            
            # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
            # do not change this unless explicitly requested by the user
            response = self.openai_client.chat.completions.create(
                model="gpt-5",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content or "I apologize, but I couldn't generate a response."
            
        except Exception as e:
            st.error(f"AI response error: {str(e)}")
            return self.generate_fallback_response(user_message)
    
    def generate_fallback_response(self, user_message: str) -> str:
        """Generate fallback response when OpenAI is not available"""
        user_message_lower = user_message.lower()
        
        # Query relevant data
        data_context = self.query_inventory_data(user_message)
        
        # Check what type of query this is and provide appropriate response
        if any(phrase in user_message_lower for phrase in [
            'which items should i reorder', 'reorder this week', 'reorder suggestions', 'need to reorder'
        ]):
            try:
                inventory_df = self.db.get_inventory()
                low_stock = inventory_df[inventory_df['current_stock'] < inventory_df['min_stock_level']]
                if low_stock.empty:
                    return "No immediate reorders suggested. All items are above minimum stock levels."
                top_needed = low_stock.copy()
                top_needed['gap'] = top_needed['min_stock_level'] - top_needed['current_stock']
                top_needed = top_needed.sort_values('gap', ascending=False).head(10)
                lines = ["Suggested reorders (top 10 by gap):\n"]
                for _, row in top_needed.iterrows():
                    lines.append(f"• {row['drug_name']} — Current: {row['current_stock']}, Min: {row['min_stock_level']} (Order ≈ {max(int(row['gap']*1.5), 1)})")
                lines.append("\nTip: Use Smart Reordering page for AI-prioritized suggestions.")
                return "\n".join(lines)
            except Exception:
                return "I couldn't compute reorder suggestions right now. Please try the Smart Reordering page."

        if any(phrase in user_message_lower for phrase in [
            'expiring in the next 7 days', 'expiring this week', 'next 7 days'
        ]):
            try:
                expiring_7 = self.db.get_expiring_drugs(days_ahead=7)
                if not expiring_7:
                    return "No items expiring in the next 7 days."
                lines = ["Items expiring within 7 days:\n"]
                for item in expiring_7[:10]:
                    lines.append(f"• {item['drug_name']} (Batch {item['batch_number']}) — Expires: {item['expiry_date']}")
                return "\n".join(lines)
            except Exception:
                return "I couldn't fetch 7‑day expiry data right now."

        if 'check interactions' in user_message_lower or 'interaction between' in user_message_lower:
            try:
                # Extract two drug names naively by splitting around 'between' or 'and'
                text = user_message
                parts = text.split('between')[-1] if 'between' in text.lower() else text
                tokens = [t.strip(' ,.?') for t in parts.replace(' and ', ',').split(',') if t.strip()]
                drugs = [t for t in tokens if len(t) > 1][:2]
                known = self.db.get_known_interactions()
                if not known.empty and len(drugs) == 2:
                    d1, d2 = drugs[0], drugs[1]
                    mask = (
                        ((known['drug1'].str.lower()==d1.lower()) & (known['drug2'].str.lower()==d2.lower())) |
                        ((known['drug1'].str.lower()==d2.lower()) & (known['drug2'].str.lower()==d1.lower()))
                    )
                    matches = known[mask]
                    if not matches.empty:
                        row = matches.iloc[0]
                        return (
                            f"Interaction found for {d1} + {d2}:\n"
                            f"• Severity: {row.get('severity','N/A')}\n"
                            f"• Description: {row.get('description','N/A')}\n"
                            f"• Clinical Effect: {row.get('clinical_effect','N/A')}\n"
                            f"• Management: {row.get('management','N/A')}"
                        )
                return "No interaction found in the local database. Please verify on the Drug Interactions page for AI analysis."
            except Exception:
                return "I couldn't check interactions right now. Please try the Drug Interactions page."

        if 'find substitutes' in user_message_lower or 'substitutes for' in user_message_lower:
            try:
                # Basic availability hint
                inventory_df = self.db.get_inventory()
                lines = ["Here are some in-stock items you might consider (by category/availability):\n"]
                top = inventory_df.sort_values('current_stock', ascending=False).head(10)
                for _, row in top.iterrows():
                    lines.append(f"• {row['drug_name']} — Stock: {row['current_stock']} (Category: {row['category']})")
                lines.append("\nFor clinically equivalent substitutes, use the Drug Interactions page's substitution finder.")
                return "\n".join(lines)
            except Exception:
                return "I couldn't suggest substitutes now. Please try the Drug Interactions page."

        if 'demand forecast' in user_message_lower or 'forecast for' in user_message_lower:
            try:
                # Try to infer a drug name as last token > 2 chars
                words = [w.strip(' ,.?') for w in user_message.split()]
                candidate = words[-1] if words else None
                if candidate:
                    hist = self.db.get_historical_consumption(candidate)
                    if len(hist) >= 7:
                        avg = float(hist['consumption'].tail(14).mean()) if len(hist) >= 14 else float(hist['consumption'].mean())
                        return f"A quick heuristic forecast for {candidate}: average daily demand ≈ {avg:.1f}. For full ML forecast, open the AI Forecasting page."
                return "Provide a drug name (e.g., 'forecast for Metformin') or use the AI Forecasting page."
            except Exception:
                return "I couldn't compute a quick forecast. Use the AI Forecasting page instead."

        if 'wastage' in user_message_lower and any(k in user_message_lower for k in ['last 90 days','90 days','quarter']):
            try:
                from datetime import datetime, timedelta
                start = datetime.now() - timedelta(days=90)
                end = datetime.now()
                wastage_df = self.db.get_wastage_analysis(start, end)
                if wastage_df.empty:
                    return "No wastage recorded in the last 90 days."
                total_val = float(wastage_df['wasted_value'].sum())
                top = wastage_df.sort_values('wasted_value', ascending=False).head(5)
                lines = [f"Total wastage (90 days): ₹{total_val:,.2f}\nTop categories:"]
                for _, r in top.iterrows():
                    lines.append(f"• {r['category']}: ₹{float(r['wasted_value']):,.2f}")
                return "\n".join(lines)
            except Exception:
                return "I couldn't compute wastage right now."

        if 'budget' in user_message_lower and 'actual' in user_message_lower:
            try:
                budget = self.db.get_budget_analysis()
                if not budget:
                    return "No budget data available."
                lines = ["Budget vs Actual (by category):\n"]
                for cat, vals in budget.items():
                    lines.append(f"• {cat}: Budget ₹{vals.get('budgeted',0):,.0f} vs Actual ₹{vals.get('actual',0):,.0f}")
                return "\n".join(lines)
            except Exception:
                return "I couldn't fetch budget data right now."

        if 'anomal' in user_message_lower:
            try:
                anomalies = self.db.detect_anomalies()
                if not anomalies:
                    return "No anomalies detected in recent data."
                lines = ["Recent anomalies:"]
                for a in anomalies[:5]:
                    lines.append(f"• [{a.get('severity','info').title()}] {a.get('description','')} ")
                return "\n".join(lines)
            except Exception:
                return "I couldn't check anomalies right now."

        if any(word in user_message_lower for word in ['stock', 'level', 'inventory']):
            if 'low_stock_items' in data_context and data_context['low_stock_items']:
                items = data_context['low_stock_items']
                response = f"I found {len(items)} items with low stock:\n\n"
                for item in items[:5]:
                    response += f"• {item['drug_name']}: {item['current_stock']} units (min: {item['min_stock_level']})\n"
                return response
            else:
                return "All items appear to be adequately stocked. No low stock alerts at the moment."
        
        elif any(word in user_message_lower for word in ['expiry', 'expire', 'expiring']):
            if 'expiring_items' in data_context and data_context['expiring_items']:
                items = data_context['expiring_items']
                response = f"I found {len(items)} items expiring soon:\n\n"
                for item in items[:5]:
                    response += f"• {item['drug_name']} (Batch: {item['batch_number']}) - Expires: {item['expiry_date']}\n"
                return response
            else:
                return "No items are expiring in the next 30 days."
        
        elif any(word in user_message_lower for word in ['drug', 'medicine', 'medication']):
            if 'matching_drugs' in data_context and data_context['matching_drugs']:
                items = data_context['matching_drugs']
                response = f"I found {len(items)} matching drugs:\n\n"
                for item in items[:3]:
                    response += f"• {item['drug_name']} - Stock: {item['current_stock']} units - Price: ₹{item['unit_price']:.2f}\n"
                return response
            else:
                return "I couldn't find any matching drugs in the current inventory."
        
        elif any(word in user_message_lower for word in ['transaction', 'sale', 'recent']):
            if 'recent_transactions' in data_context and data_context['recent_transactions']:
                transactions = data_context['recent_transactions']
                response = f"Recent transactions:\n\n"
                for txn in transactions[:5]:
                    response += f"• {txn['transaction_type']}: {txn['drug_name']} - Qty: {txn['quantity']} - ₹{txn['total_amount']:.2f}\n"
                return response
            else:
                return "No recent transactions found."
        
        else:
            return "I'm here to help with your pharmaceutical inventory management. Ask me about stock levels, expiring items, drug information, or recent transactions!"
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        st.session_state.chat_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        })
        
        # Keep only last 20 messages to manage memory
        if len(st.session_state.chat_history) > 20:
            st.session_state.chat_history = st.session_state.chat_history[-20:]
    
    def get_suggested_questions(self) -> List[str]:
        """Get suggested questions based on current inventory state"""
        try:
            suggestions = []
            
            # Check for low stock items
            inventory_df = self.db.get_inventory()
            low_stock_items = len(inventory_df[inventory_df['current_stock'] < inventory_df['min_stock_level']])
            if low_stock_items > 0:
                suggestions.append("Which items are running low on stock?")
            
            # Check for expiring items
            expiring_items = self.db.get_expiring_drugs(days_ahead=30)
            if len(expiring_items) > 0:
                suggestions.append("What medications are expiring soon?")
            
            # Always available suggestions (expanded)
            suggestions.extend([
                "Show me the most expensive items in inventory",
                "What are my recent transactions?",
                "Which suppliers do I order from most?",
                "What's the total value of my inventory?",
                "Which items should I reorder this week?",
                "Any items expiring in the next 7 days?",
                "Check interactions between Paracetamol and Ibuprofen",
                "Find substitutes for Amoxicillin due to stockout",
                "Give me demand forecast for Metformin for 30 days",
                "Summarize wastage in the last 90 days",
                "Show budget vs actual spend by category",
                "Any anomalies or unusual consumption detected?"
            ])
            
            return suggestions[:12]  # Return up to 12 suggestions
            
        except Exception as e:
            return ["How can I help you with your inventory today?"]

def render_ai_chatbot_page(db):
    """Render the AI chatbot page"""
    st.title("🤖 AI Pharmaceutical Assistant")
    st.markdown("Ask me anything about your pharmaceutical inventory, drug information, or system insights!")
    
    # Initialize chatbot
    chatbot = PharmaceuticalChatbot(db)
    
    # Check if OpenAI is available
    if not OPENAI_AVAILABLE or not os.environ.get("OPENAI_API_KEY"):
        st.info("💡 **Enhanced AI Features Available**: Connect your OpenAI API key for advanced conversational capabilities and detailed pharmaceutical insights!")
        with st.expander("ℹ️ How to enable advanced AI features"):
            st.markdown("""
            1. Get an OpenAI API key from [OpenAI Platform](https://platform.openai.com)
            2. Add it to your Replit secrets as `OPENAI_API_KEY`
            3. Restart the application to enable advanced AI features
            
            Even without OpenAI, I can still help with basic inventory queries using your database!
            """)
    
    # Suggested questions
    st.subheader("💡 Suggested Questions")
    suggestions = chatbot.get_suggested_questions()

    cols = st.columns(3)
    for i, suggestion in enumerate(suggestions):
        col = cols[i % 3]
        if col.button(suggestion, key=f"suggestion_{i}"):
            # Add suggestion to chat
            chatbot.add_to_history("user", suggestion)
            # Get and add response
            response = chatbot.generate_ai_response(suggestion)
            chatbot.add_to_history("assistant", response)
            st.rerun()
    
    st.divider()
    
    # Chat interface
    st.subheader("💬 Chat with AI Assistant")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for i, message in enumerate(st.session_state.chat_history):
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me about your pharmaceutical inventory..."):
        # Add user message to history
        chatbot.add_to_history("user", prompt)
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chatbot.generate_ai_response(prompt)
                st.write(response)
                
                # Add assistant response to history
                chatbot.add_to_history("assistant", response)
    
    # Chat controls
    st.sidebar.markdown("### 🛠️ Chat Controls")
    if st.sidebar.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()
    
    # Chat statistics
    if st.session_state.chat_history:
        st.sidebar.markdown(f"**Messages:** {len(st.session_state.chat_history)}")
        st.sidebar.markdown(f"**Conversation started:** {st.session_state.chat_history[0]['timestamp'].strftime('%H:%M')}")
    
    # Quick actions
    st.sidebar.markdown("### ⚡ Quick Actions")
    if st.sidebar.button("📊 Current Inventory Status"):
        status_query = "Give me a summary of my current inventory status"
        chatbot.add_to_history("user", status_query)
        response = chatbot.generate_ai_response(status_query)
        chatbot.add_to_history("assistant", response)
        st.rerun()
    
    if st.sidebar.button("⚠️ Check Alerts"):
        alerts_query = "What alerts or issues should I be aware of?"
        chatbot.add_to_history("user", alerts_query)
        response = chatbot.generate_ai_response(alerts_query)
        chatbot.add_to_history("assistant", response)
        st.rerun()