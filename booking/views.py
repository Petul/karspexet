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

def determine_price(spex, nachspex, guest_type, alcohol_free, coupon):
    prices = {
        'phux': 10,
        'student': 15,
        'other': 25
    }
    price = 0
    if spex:
        if coupon:
            price += coupon.price
        else:
            price += prices[guest_type]
    if nachspex:
        if spex:
            price += 15
        else:
            price += 18
        # If alcoholfree price is reduced by 3€
        if alcohol_free:
            price -= 3

    print(price)
    return price


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

def coupon(request, coupon_code):
    if DiscountCode.objects.filter(code = coupon_code).exists():
        coupon = DiscountCode.objects.get(code = coupon_code)
        #return discount code information
        return render(request, 'coupon.html', {'times_used': coupon.times_used, 'uses': coupon.uses, 'price': coupon.price})
    else:
        return render(request, 'index.html', {'error_message': "Det existerar inte en kupong för koden du angett"})
        #return error message

def thanks(request):
    return render(request, "thanks.html")

def form_page_view(request):
    return render(request, "index.html")

def register(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = registerForm(request.POST)
        # check whether it's valid:
        if form.is_valid():

            form = form.cleaned_data
            if form['student'] == 'student':
                guest_type = 'student'
            elif form['student'] == 'phux':
                guest_type = 'phux'
            else:
                guest_type = 'other'

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

            coupon_code = form['coupon']
            coupon_valid = False
            coupon_expired = False
            coupon_used = 0
            coupon_total_uses = 0

            if coupon_code != "":
                coupon_entered = True
                if DiscountCode.objects.filter(code=coupon_code).exists(): #Check if a code exists
                    coupon = DiscountCode.objects.get(code=form['coupon'])
                    if not coupon.is_used():
                        coupon_valid = True
                        coupon_used = coupon.times_used
                        coupon_total_uses = coupon.uses
                    else:
                        coupon_expired = False
                        coupon_valid = False
                        coupon = None
                else:
                    coupon_valid = False
                    coupon = None
            else:
                coupon = None
                coupon_entered = False

            cheaper_price_available = False
            if guest_type == 'phux' and coupon != None:
                if coupon.price >= 10:
                    coupon = None
                    cheaper_price_available = True
                    coupon_entered = False

            price = determine_price(spex, nachspex, guest_type, form['alcoholFree'], coupon)


            context = {
                'name': form['name'],
                'email': form['email'],
                'avec': form['avec'],
                'diet': form['diet'],
                'comment': form['comment'],
                'alcohol_free' : form['alcoholFree'],
                'register_choice': register_choice,
                'spex': spex,
                'student': guest_type,
                'nachspex': nachspex,
                'price': price,
                'coupon_valid': coupon_valid,
                'coupon_code': coupon_code,
                'coupon_entered': coupon_entered,
                'coupon_expired': coupon_expired,
                'coupon_used': coupon_used,
                'coupon_total_uses': coupon_total_uses,
                'cheaper_price_available': cheaper_price_available,
                }
            return render(request, 'confirm.html', context)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = registerForm()
    return render(request, 'register.html', {'form': form})

def send(request):
    if request.method == 'POST':
        comment = request.POST['comment']
        name = request.POST['name']
        email = request.POST['email']
        spex = request.POST['spex']
        nachspex = request.POST['nachspex']
        coupon = request.POST['coupon']
        alcohol_free = request.POST['alcohol_free']
        avec = request.POST['avec']
        diet = request.POST['diet']
        guest_type = request.POST['student']

        if DiscountCode.objects.filter(code=coupon).exists():
            coupon = DiscountCode.objects.get(code=coupon)
            if not coupon.is_used():
                coupon.times_used += 1
                coupon.save()
            else:
                coupon = None
        else:
            coupon = None

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

        if guest_type == 'phux' and coupon != None:
            if coupon.price >= 10:
                coupon = None

        price = determine_price(spex, nachspex, guest_type, alcohol_free, coupon)

        new_participant = Participant(
            name=name,
            email=email,
            spex=spex,
            nachspex=nachspex,
            alcoholfree=alcohol_free,
            diet=diet,
            avec=avec,
            comment=comment,
            student=guest_type,
            price=price
        )

        new_participant.uuid = uuid.uuid4()
        new_participant.save()
        ticket_url = 'https://karspex.teknologforeningen.fi/ticket/'+str(new_participant.uuid)
        subject, sender = 'Anmälan till Kårspexets föreställning', 'Kårspexambassaden <karspex@teknolog.fi>'
        content = "Tack för din anmälan till Kårspexets Finlandsföreställning den 10 februari. \n Din biljett hittar du på "+ ticket_url +". Vänligen ta fram biljetten när du går in i teatern för att försnabba inträdet. \n Betala " + str(price) + " € till konto FI02 5723 0220 4788 41 (mottagare Kårspexambassaden) med för- och efternamn som meddelande. Betalningen ska vara framme senast 9.2.2018. Ifall betalningen inte hinner till detta, ber vi dig vänligen ta med jämna pengar till teatern.\n\nMed vänliga hälsningar,\nKårspexambassaden"
        if DEBUG:
            print('Subject: {}\nSender: {}\nRecipient: {}\nContent: {}'.format(subject, sender, email, content))
        else:
            send_mail(subject, content, sender, [email], fail_silently=False)

        return HttpResponseRedirect('/register/thanks/')
    else:
        return render(request, 'index.html', {'error_message': "Det skedde ett fel, vänligen försök pånytt"})
