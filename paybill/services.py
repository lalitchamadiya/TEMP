import hmac
import hashlib
import json
import uuid
from abc import ABC, abstractmethod
from django.conf import settings
from .models import Payment, GatewayConfig

class PaymentGatewayError(Exception):
    pass

class BasePaymentGateway(ABC):
    def __init__(self, config: GatewayConfig):
        self.config = config

    @abstractmethod
    def create_order(self, amount, currency='INR', **kwargs):
        """Creates an order with the gateway and returns gateway-specific order data."""
        pass

    @abstractmethod
    def verify_payment(self, params):
        """Verifies the payment response from the gateway."""
        pass

class RazorpayGateway(BasePaymentGateway):
    def create_order(self, amount, currency='INR', **kwargs):
        # In a real implementation, we would use the razorpay-python library.
        # Here we simulate the logic or use requests to their API.
        import razorpay
        client = razorpay.Client(auth=(self.config.api_key, self.config.api_secret))
        
        data = {
            'amount': int(amount * 100), # Razorpay expects amount in paise
            'currency': currency,
            'receipt': str(uuid.uuid4())[:20],
            'payment_capture': 1
        }
        try:
            return client.order.create(data=data)
        except Exception as e:
            raise PaymentGatewayError(f"Razorpay order creation failed: {str(e)}")

    def verify_payment(self, params):
        import razorpay
        client = razorpay.Client(auth=(self.config.api_key, self.config.api_secret))
        try:
            # params = {razorpay_order_id, razorpay_payment_id, razorpay_signature}
            client.utility.verify_payment_signature(params)
            return True
        except Exception:
            return False

class StripeGateway(BasePaymentGateway):
    def create_order(self, amount, currency='INR', **kwargs):
        import stripe
        stripe.api_key = self.config.api_secret
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency=currency.lower(),
                metadata={'student_id': kwargs.get('student_id')}
            )
            return {'id': intent.id, 'client_secret': intent.client_secret}
        except Exception as e:
            raise PaymentGatewayError(f"Stripe intent creation failed: {str(e)}")

    def verify_payment(self, params):
        import stripe
        # Stripe verification usually happens via webhooks or checking the intent status
        stripe.api_key = self.config.api_secret
        try:
            intent = stripe.PaymentIntent.retrieve(params.get('payment_intent_id'))
            return intent.status == 'succeeded'
        except Exception:
            return False

class DemoGateway(BasePaymentGateway):
    def create_order(self, amount, currency='INR', **kwargs):
        """Simulates order creation locally."""
        return {
            'id': f"ORD_DEMO_{uuid.uuid4().hex[:10].upper()}",
            'amount': amount,
            'currency': currency,
            'status': 'created'
        }

    def verify_payment(self, params):
        """Simulates verification. In demo mode, we accept the mock signature."""
        mock_signature = params.get('demo_signature')
        # In a real demo, we could check if it matches a generated value, 
        # but for simplicity, any demo_signature is valid.
        return mock_signature == "DEMO_SUCCESS_SIG"

class PaymentGatewayFactory:
    @staticmethod
    def get_gateway(gateway_name=None):
        if gateway_name:
            config = GatewayConfig.objects.filter(name=gateway_name, is_active=True).first()
        else:
            config = GatewayConfig.objects.filter(is_active=True).first()
            
        if not config:
            # Fallback to demo if no config exists, or raise error
            raise PaymentGatewayError("No active payment gateway configuration found.")
            
        if config.name == 'razorpay':
            return RazorpayGateway(config)
        elif config.name == 'stripe':
            return StripeGateway(config)
        elif config.name == 'demo':
            return DemoGateway(config)
        # Add other gateways here
        raise PaymentGatewayError(f"Gateway {config.name} is not implemented yet.")
