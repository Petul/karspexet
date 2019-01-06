from django import forms
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template import RequestContext
from booking.models import *
from django.contrib.auth.decorators import login_required
from karspexet.settings import DEBUG
import datetime, math
import uuid

from .forms import registerForm

def verify_coupon(coupon_code):
    '''
    @param: A code for a coupon. Max 8 characters (str)
    @return: Tuple with:
                - statuscode (int)
                - coupon if found, otherwise None (DiscountCode)
    Statuscodes:
        1: All good
        -1: DiscountCode doesn't exist
        -2: Coupon is used
    '''
    try:
        coupon = DiscountCode.objects.get(code=coupon_code)
    except models.ObjectDoesNotExist:
        return (-1, None)
    if coupon.is_used():
        return (-2, coupon)
    return (1, coupon)


def determine_price(spex, nachspex, guest_type, alcohol_free, coupon=None):
    prices = {
        'phux': 10,
        'student': 15,
        'not_student': 25
    }
    price = 0
    cheaper_used = False
    if spex:
        '''
        Use coupon if and only if:
            - It exists
            - It's still valid (still has uses left)
            - The price is less than it otherwise would be
        '''
        if coupon and not coupon.is_used() and coupon.price < prices[guest_type]:
            price += coupon.price
        else:
            price += prices[guest_type]
            if coupon and coupon.price >= prices[guest_type]:
                cheaper_used = True

    # Price for nachspex is 15€ if also spex and 18€ if only nachspex
    if nachspex:
        if spex:
            price += 15
        else:
            price += 18
        # If alcoholfree price is reduced by 3€
        if alcohol_free:
            price -= 3
    return (price, cheaper_used)


# Create your views here.
@login_required(login_url='/admin')
def enrolled(request):
    return render(request, 'enrolled.html', {'participants': Participant.objects.all()})

def ticket(request, participant_id):
    if Participant.objects.filter(uuid = participant_id).exists():
        participant = Participant.objects.get(uuid = participant_id)

        context = {
        'name': participant.name,
        'student': participant.student,
        'spex': participant.spex,
        'nachspex': participant.nachspex,
        'price': participant.price,
        }

        return render(request, 'ticket.html', context)
    else:
        return render(request, 'index.html', {'error_message': "Det existerar inte biljett med denna id"})

def thanks(request):
    return render(request, "thanks.html")

def form_page_view(request):
    return render(request, "index.html")

def register(request):
    if request.method == 'POST':
        form = registerForm(request.POST)
        if form.is_valid():
            form = form.cleaned_data
            # Check type of ticket
            if form['register_choice'] == 'only_spex':
                register_choice = "Endast spex"
                spex = True
                nachspex = False
            elif form['register_choice'] == 'only_nachspex':
                register_choice = "Endast nachspex"
                spex = False
                nachspex = True
            else:
                register_choice = "Spex och nachspex"
                spex = True
                nachspex = True

            # Check validity of coupon if code was entered
            status_code, coupon = None, None
            if form['coupon']:
                status_code, coupon = verify_coupon(form['coupon'])

            # Check price
            price, cheaper_used = determine_price(spex, nachspex, form['student'], form['alcoholFree'], coupon)
            if cheaper_used:
                status_code = 0

            context = {
                'name': form['name'],
                'email': form['email'],
                'avec': form['avec'],
                'diet': form['diet'],
                'comment': form['comment'],
                'alcohol_free' : form['alcoholFree'],
                'register_choice': register_choice,
                'spex': spex,
                'student': form['student'],
                'nachspex': nachspex,
                'price': price,
                'coupon_status': status_code,
                'coupon_code': form['coupon']
            }
            return render(request, 'confirm.html', context)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = registerForm()
    return render(request, 'register.html', {'form': form})

def send(request):
    if request.method == 'POST':
        spex = request.POST['spex']
        nachspex = request.POST['nachspex']
        coupon_code = request.POST['coupon']
        alcohol_free = request.POST['alcohol_free']
        guest_type = request.POST['student']
        email = request.POST['email']

        # Apparently the 'True' is not a Boolean and needs to be converted, wtf
        # TODO: Change to 0 and 1 to avoid this step
        if nachspex == 'True':
            nachspex = True
        else:
            nachspex = False

        if spex == 'True':
            spex = True
        else:
            spex = False

        if alcohol_free == 'True':
            alcohol_free = True
        else:
            alcohol_free = False

        status_code, coupon = None, None
        if request.POST['coupon']:
            status_code, coupon = verify_coupon(request.POST['coupon'])
        price, cheaper_used = determine_price(spex, nachspex, guest_type, alcohol_free, coupon)


        new_participant = Participant(
            name=request.POST['name'],
            email=email,
            spex=spex,
            nachspex=nachspex,
            alcoholfree=alcohol_free,
            diet=request.POST['diet'],
            avec=request.POST['avec'],
            comment=request.POST['comment'],
            student=guest_type,
            price=price,
            uuid=uuid.uuid4()
        )
        new_participant.save()

        if status_code == 1 and not cheaper_used:
            coupon.times_used += 1
            coupon.save()

        ticket_url = 'https://karspex.teknologforeningen.fi/ticket/{}'.format(new_participant.uuid)
        subject, sender = 'Anmälan till Kårspexets föreställning', 'Kårspexambassaden <karspex@teknolog.fi>'
        content = "Tack för din anmälan till Kårspexets Finlandsföreställning den 23 februari.\nDin biljett hittar du på {}. Vänligen ta fram biljetten när du går in i teatern för att försnabba inträdet.\nBetala {}€ till konto FI02 5723 0220 4788 41 (mottagare Kårspexambassaden) med meddelandet \"Kårspex, Förnamn Efternamn\". Betalningen ska vara framme senast 22.2.2019. Ifall betalningen inte hinner till detta, ber vi dig vänligen ta med jämna pengar till teatern.\n\nMed vänliga hälsningar,\nKårspexambassaden.".format(ticket_url, price)
        if DEBUG:
            print('Subject: {}\nSender: {}\nRecipient: {}\nContent: {}'.format(subject, sender, email, content))
        else:
            send_mail(subject, content, sender, [email], fail_silently=False)

        return HttpResponseRedirect('/register/thanks/')
    else:
        return render(request, 'index.html', {'error_message': "Det skedde ett fel, vänligen försök pånytt"})
