from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import Http404
from requests.exceptions import ConnectionError

from .services.RFQCreator import RFQCreator
from .forms import RFQForm
from .forms import RFQInternalCode

import requests
import json
import os

from common.BackendMessage import BackendMessage
from common.MachineConfig import MachineConfigurator
from common.Instructions import Instructions
from common.FrontendTexts import FrontendTexts


view_texts = FrontendTexts('rfqs')


def cleanup(filename):
    try:
        os.remove('.' + filename)
        print("removed file: " + filename)
    except Exception as error:
        print(error)


@login_required(login_url='/auth/login')
def rfq_upload(request):
    menu_texts = FrontendTexts('menu')
    instructions = Instructions('rfqs', 'upload')
    uploaded_file_url = ''
    try:

        if request.method == 'POST':
            form = RFQForm(request.POST, request.FILES)
            if form.is_valid():

                rfq = RFQCreator()

                internal_code = form.cleaned_data['internalCode']
                external_code = form.cleaned_data['externalCode']
                sender = form.cleaned_data['sender']
                company = form.cleaned_data['company']
                received_date = form.cleaned_data['receivedDate']
                note = form.cleaned_data['note']

                rfq.setRFQInformation(internal_code, external_code, sender, company, received_date)
                rfq.addRFQNote(note)

                myfile = request.FILES['document']
                fs = FileSystemStorage()
                filename = fs.save(myfile.name, myfile)
                uploaded_file_url = fs.url(filename)

                result = rfq.createRFQfromCSV('.' + uploaded_file_url)

                # ... print(json.dumps(result))

                backend_host = MachineConfigurator().getBackend()
                r = requests.post(backend_host + '/auth/rfqs/', json=result)

                backend_message = BackendMessage(json.loads(r.text))

                cleanup(uploaded_file_url)

                return render(request, 'rfqs/rfq_upload.html', {'menu_text': menu_texts.getComponent(),
                                                                'view_texts': view_texts.getComponent(),
                                                                'form': form,
                                                                'error_message': backend_message.getValue()})
        else:
            form = RFQForm()
        return render(request, 'rfqs/rfq_upload.html', {'menu_text': menu_texts.getComponent(),
                                                        'view_texts': view_texts.getComponent(),
                                                        'form': form,
                                                        'instructions_title': instructions.getTitle(),
                                                        'instructions_steps': instructions.getSteps()
                                                        })

    except ValueError as exception:
        cleanup(uploaded_file_url)
        print("There is a problem with the backend return value")
        print(exception)
        return render(request, 'rfqs/rfq_upload.html', {'menu_text': menu_texts.getComponent(),
                                                        'view_texts': view_texts.getComponent(),
                                                        'form': form,
                                                        'error_message': 'Backend problem',
                                                        'instructions_title': instructions.getTitle(),
                                                        'instructions_steps': instructions.getSteps()
                                                        })

    except ConnectionError as exception:
        cleanup(uploaded_file_url)
        print("There is a problem with the backend return value")
        print(exception)
        return render(request, 'rfqs/rfq_upload.html', {'menu_text': menu_texts.getComponent(),
                                                        'view_texts': view_texts.getComponent(),
                                                        'form': form,
                                                        'error_message': 'Backend connection problem',
                                                        'instructions_title': instructions.getTitle(),
                                                        'instructions_steps': instructions.getSteps()
                                                        })

    except Exception as exception:
        cleanup(uploaded_file_url)
        print(exception)
        return render(request, 'rfqs/rfq_upload.html', {'menu_text': menu_texts.getComponent(),
                                                        'view_texts': view_texts.getComponent(),
                                                        'form': form,
                                                        'error_message': "Frontend Error",
                                                        'instructions_title': instructions.getTitle(),
                                                        'instructions_steps': instructions.getSteps()
                                                        })


@login_required(login_url='/auth/login')
def rfq_export(request):
    menu_texts = FrontendTexts('menu')
    instructions = Instructions('rfqs', 'export')
    output_file = ''
    try:
        if request.method == 'POST':
            form = RFQInternalCode(request.POST)
            if form.is_valid():

                internal_code = form.cleaned_data['internalcode']

                incoterms = form.cleaned_data['incoterms']

                port = form.cleaned_data['port']

                backend_host = MachineConfigurator().getBackend()

                r = requests.get(backend_host + '/auth/rfqs/' + internal_code)

                backend_message = BackendMessage(json.loads(r.text))

                if not backend_message.getErrorInd():

                    rfq = json.loads(backend_message.getValue())
                    rfq_service = RFQCreator()
                    output_file = rfq_service.exportRFQtoCSV(rfq, incoterms, port)

                    if os.path.exists(output_file):
                        with open(output_file, 'rb') as fh:
                            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
                        cleanup('/' + output_file)
                        response['Content-Disposition'] = 'inline; filename=' + os.path.basename(output_file)
                        return response
                    raise Http404

                else:
                    print("There is a backend error message")
                    return render(request, 'rfqs/rfq_export.html', {'menu_text': menu_texts.getComponent(),
                                                                    'view_texts': view_texts.getComponent(),
                                                                    'rfqform': form,
                                                                    'error_message': backend_message.getValue(),
                                                                    'instructions_title': instructions.getTitle(),
                                                                    'instructions_steps': instructions.getSteps()
                                                                    })

        else:
            form = RFQInternalCode()

        return render(request, 'rfqs/rfq_export.html', {'menu_text': menu_texts.getComponent(),
                                                        'view_texts': view_texts.getComponent(),
                                                        'rfqform': form,
                                                        'instructions_title': instructions.getTitle(),
                                                        'instructions_steps': instructions.getSteps()
                                                        })

    except ValueError as exception:
        print("There is a problem with the backend return value")
        print(exception)
        return render(request, 'rfqs/rfq_export.html', {'menu_text': menu_texts.getComponent(),
                                                        'view_texts': view_texts.getComponent(),
                                                        'rfqform': form,
                                                        'error_message': 'Backend problem',
                                                        'instructions_title': instructions.getTitle(),
                                                        'instructions_steps': instructions.getSteps()
                                                        })

    except ConnectionError as exception:
        print("There is a problem with the backend return value")
        print(exception)
        return render(request, 'rfqs/rfq_upload.html', {'menu_text': menu_texts.getComponent(),
                                                        'view_texts': view_texts.getComponent(),
                                                        'form': form,
                                                        'error_message': 'Backend connection problem',
                                                        'instructions_title': instructions.getTitle(),
                                                        'instructions_steps': instructions.getSteps()
                                                        })

    except Exception as exception:
        cleanup(output_file)
        print(exception)
        return render(request, 'rfqs/rfq_upload.html', {'menu_text': menu_texts.getComponent(),
                                                        'view_texts': view_texts.getComponent(),
                                                        'form': form,
                                                        'error_message': "Frontend Error",
                                                        'instructions_title': instructions.getTitle(),
                                                        'instructions_steps': instructions.getSteps()
                                                        })


@login_required(login_url='/auth/login')
def rfq_qfinder(request):
    menu_texts = FrontendTexts('menu')
    instructions = Instructions('rfqs', 'qfinder')
    uploaded_file_url = ''
    try:
        if request.method == 'POST' and request.FILES['myfile']:
            myfile = request.FILES['myfile']
            fs = FileSystemStorage()
            filename = fs.save(myfile.name, myfile)
            uploaded_file_url = fs.url(filename)

            rfq = RFQCreator()
            result = rfq.findQuotesFromCSV('.' + uploaded_file_url)

            # ... print(json.dumps(result))

            backend_host = MachineConfigurator().getBackend()
            r = requests.post(backend_host + '/auth/rfqs/quotes', json=result)

            backend_message = BackendMessage(json.loads(r.text))

            if not backend_message.getErrorInd():

                quoted_materials = json.loads(backend_message.getValue())
                cleanup(uploaded_file_url)

                return render(request, 'rfqs/rfq_qfinder.html', {'menu_text': menu_texts.getComponent(),
                                                                 'view_texts': view_texts.getComponent(),
                                                                 'quoted_materials': quoted_materials,
                                                                 'instructions_title': instructions.getTitle(),
                                                                 'instructions_steps': instructions.getSteps()
                                                                 })
            else:
                print(backend_message.getValue())
                cleanup(uploaded_file_url)
                return render(request, 'rfqs/rfq_qfinder.html', {'menu_text': menu_texts.getComponent(),
                                                                 'view_texts': view_texts.getComponent(),
                                                                 'error_message': backend_message.getValue(),
                                                                 'instructions_title': instructions.getTitle(),
                                                                 'instructions_steps': instructions.getSteps()
                                                                 })

        return render(request, 'rfqs/rfq_qfinder.html', {'menu_text': menu_texts.getComponent(),
                                                         'view_texts': view_texts.getComponent(),
                                                         'instructions_title': instructions.getTitle(),
                                                         'instructions_steps': instructions.getSteps()
                                                         })

    except ConnectionError as exception:
        print("There is a problem with the backend return value")
        print(exception)
        return render(request, 'rfqs/rfq_qfinder.html', {'menu_text': menu_texts.getComponent(),
                                                         'view_texts': view_texts.getComponent(),
                                                         'error_message': 'Backend connection problem',
                                                         'instructions_title': instructions.getTitle(),
                                                         'instructions_steps': instructions.getSteps()
                                                         })

    except Exception as exception:
        cleanup(uploaded_file_url)
        print(exception)
        return render(request, 'rfqs/rfq_qfinder.html', {'menu_text': menu_texts.getComponent(),
                                                         'view_texts': view_texts.getComponent(),
                                                         'error_message': "Frontend Error",
                                                         'instructions_title': instructions.getTitle(),
                                                         'instructions_steps': instructions.getSteps()
                                                         })
