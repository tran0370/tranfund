from django.shortcuts import render, get_object_or_404, redirect
from .forms import CustomSignupForm
from django.urls import reverse_lazy
from django.views import generic
from .models import FitnessPlan, Customer
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
import stripe
from django.http import HttpResponse
from plaid import Client
import os

# public_token: public-sandbox-19357099-303a-40d3-9c5e-d1c74eb0eb34 checkout: 108: 23
# account ID: 3ERywNB85Nf8R1w19a1zuWzdvjjaPBTqERblo

stripe_pub_key = os.environ.get('stripe_publickey')
stripe_sec_key = os.environ.get('stripe_secretkey')
plaid_client = os.environ.get('plaid_clientid')
plaid_pub_key = os.environ.get('plaid_publickey')
plaid_dev_key = os.environ.get('plaid_development')
plaid_sb_key = os.environ.get('plaid_sandbox')


@user_passes_test(lambda u: u.is_superuser)
def updateaccounts(request):
    customers = Customer.objects.all()
    for customer in customers:
        subscription = stripe.Subscription.retrieve(
            customer.stripe_subscription_id)
        if subscription.status != 'active':
            membership = False
        else:
            customer.membership = True
        customer.cancel_at_period_end = subscription.cancel_at_period_end
        customer.save()
        return HttpResponse('completed')


def home(request):
    plans = FitnessPlan.objects
    return render(request, 'plans/home.html', {'plans': plans})


def plan(request, pk):
    plan = get_object_or_404(FitnessPlan, pk=pk)
    if plan.premium:

        if request.user.is_authenticated:
            try:
                if request.user.customer.membership:
                    return render(request, 'plans/plan.html', {'plan': plan})
            except Customer.DoesNotExist:
                return redirect('join')
        return redirect('join')
    else:
        return render(request, 'plans/plan.html', {'plan': plan})


def join(request):
    return render(request, 'plans/join.html')


@login_required
def checkout(request):

    try:
        if request.user.customer.membership:
            return redirect('settings')
    except Customer.DoesNotExist:
        pass

    coupons = {'halloween': 31, 'welcome': 10}

    if request.method == 'POST':
        stripe_customer = stripe.Customer.create(
            email=request.user.email, source=request.POST['stripeToken'])
        plan = 'plan_Fn9qTkHvVOHVgw'
        if request.POST['plan'] == 'yearly':
            plan = 'plan_Fn9r1J14oOuPTN'
        if request.POST['coupon'] in coupons:
            percentage = coupons[request.POST['coupon'].lower()]
            try:
                coupon = stripe.Coupon.create(
                    duration='once', id=request.POST['coupon'].lower(), percent_off=percentage)
            except:
                pass
            subscription = stripe.Subscription.create(
                customer=stripe_customer.id, items=[{'plan': plan}], coupon=request.POST['coupon'].lower())
        else:
            subscription = stripe.Subscription.create(
                customer=stripe_customer.id, items=[{'plan': plan}])

        customer = Customer()
        customer.user = request.user
        customer.stripeid = stripe_customer.id
        customer.membership = True
        customer.cancel_at_period_end = False
        customer.stripe_subscription_id = subscription.id
        customer.save()

        return redirect('home')
    else:
        plan = 'Five'
        coupon = 'none'
        price = 500
        og_dollar = 5
        coupon_dollar = 0
        final_dollar = 5
        if request.method == 'GET' and 'plan' in request.GET:
            if request.GET['plan'] == 'yearly':
                plan = 'yearly'
                price = 10000
                og_dollar = 100
                final_dollar = 100
            if request.GET['plan'] == 'Ten':
                plan = 'Ten'
                price = 1000
                og_dollar = 10
                final_dollar = 10
            if request.GET['plan'] == 'Fifteen':
                plan = 'Fifteen'
                price = 1500
                og_dollar = 15
                final_dollar = 15
            if request.GET['plan'] == 'Twenty':
                plan = 'Twenty'
                price = 2000
                og_dollar = 20
                final_dollar = 20
            if request.GET['plan'] == 'Twenty-Five':
                plan = 'Twenty-Five'
                price = 2500
                og_dollar = 25
                final_dollar = 25
            if request.GET['plan'] == 'Thirty':
                plan = 'Thirty'
                price = 3000
                og_dollar = 30
                final_dollar = 30
            if request.GET['plan'] == 'Forty':
                plan = 'Forty'
                price = 4000
                og_dollar = 40
                final_dollar = 40
            if request.GET['plan'] == 'Fifty':
                plan = 'Fifty'
                price = 5000
                og_dollar = 50
                final_dollar = 50
            if request.GET['plan'] == 'One-Hundred':
                plan = 'One-Hundred'
                price = 10000
                og_dollar = 100
                final_dollar = 100
            if request.GET['plan'] == 'Two-Hundred':
                plan = 'Two-Hundred'
                price = 20000
                og_dollar = 200
                final_dollar = 200

        if request.method == 'GET' and 'coupon' in request.GET:
            if request.GET['coupon'].lower() in coupons:
                coupon = request.GET['coupon'].lower()
                percentage = coupons[coupon]
                coupon_price = int((percentage/100) * price)
                price = price - coupon_price
                coupon_dollar = str(coupon_price)[
                    :-2] + '.' + str(coupon_price)[-2:]
                final_dollar = str(price)[:-2] + '.' + str(price)[-2:]

        return render(request, 'plans/checkout.html', {
            'plan': plan,
            'coupon': coupon,
            'price': price,
            'og_dollar': og_dollar,
            'coupon_dollar': coupon_dollar,
            'final_dollar': final_dollar
        })


def settings(request):
    membership = False
    cancel_at_period_end = False

    if request.method == 'POST':
        subscription = stripe.Subscription.retrieve(
            request.user.customer.stripe_subscription_id)
        subscription.cancel_at_period_end = True
        request.user.customer.cancel_at_period_end = True
        cancel_at_period_end = True
        subscription.save()
        request.user.customer.save()
    else:
        try:
            if request.user.customer.membership:
                membership = True
            if request.user.customer.cancel_at_period_end:
                cancel_at_period_end = True
        except Customer.DoesNotExist:
            membership = False
    return render(request, 'registration/settings.html', {'membership': membership, 'cancel_at_period_end': cancel_at_period_end})


class SignUp(generic.CreateView):
    form_class = CustomSignupForm
    success_url = reverse_lazy('home')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        valid = super(SignUp, self).form_valid(form)
        username, password = form.cleaned_data.get(
            'username'), form.cleaned_data.get('password1')
        new_user = authenticate(username=username, password=password)
        login(self.request, new_user)
        return valid

# Below we are testing stripe


def deliver(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        public_token = data.get('public_token')
        account_ID = data.get('account ID')

        client = Client(plaid_client,
                        plaid_sb_key,
                        plaid_pub_key,
                        'sandbox')

        exchange_token_response = client.Item.public_token.exchange(
            public_token)
        access_token = exchange_token_response['access_token']

        stripe_response = client.Processor.stripeBankAccountTokenCreate(
            access_token, account_ID)
        bank_account_token = stripe_response['stripe_bank_account_token']
