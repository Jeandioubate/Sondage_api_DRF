
from django.db.models import F
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.views import generic
from django.urls import reverse
from django.db.models import Sum, Max

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .serializers import QuestionSerializer


from .forms import QuestionForm
from django.utils import timezone

from .models import Question, Choice

# Create your views here.

class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")

class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))

def all_polls(request):
    questions = Question.objects.all()
    context = {
        'questions': questions
    }
    return render(request, 'polls/all.html', context)

def frequency(request, question_id):
    question = get_object_or_404(Question, pk=question_id)

    choices = question.choice_set.all()
    total_votes = sum(choice.votes for choice in choices)

    results = []
    for choice in choices:
        if total_votes > 0:
            percentage = (choice.votes / total_votes) * 100
        else:
            percentage = 0
        results.append((choice, percentage))

    context = {
        'question': question,
        'results': results,
        'total_votes': total_votes,
    }
    return render(request, 'polls/frequency.html', context)

def statistics(request):
    total_questions = Question.objects.count()
    total_choices = Choice.objects.count()
    total_votes = Choice.objects.aggregate(total=Sum('votes'))['total'] or 0

    average_votes = (
        total_votes / total_questions if total_questions > 0 else 0
    )

    most_popular = Question.most_popular()
    least_popular = Question.least_popular()

    last_question = Question.objects.aggregate(
        last_date=Max('pub_date')
    )
    last_question = Question.objects.filter(
        pub_date=last_question['last_date']
    ).first()

    context = {
        'total_questions': total_questions,
        'total_choices': total_choices,
        'total_votes': total_votes,
        'average_votes': average_votes,
        'most_popular': most_popular,
        'least_popular': least_popular,
        'last_question': last_question,
    }
    return render(request, 'polls/statistics.html', context)

def create_question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save()

            choices = [
                form.cleaned_data.get('choice1'),
                form.cleaned_data.get('choice2'),
                form.cleaned_data.get('choice3'),
                form.cleaned_data.get('choice4'),
                form.cleaned_data.get('choice5'),
            ]

            for choice_text in choices:
                if choice_text:
                    Choice.objects.create(
                        question=question,
                        choice_text=choice_text,
                        votes=0
                    )
            return redirect('polls:index')
    else:
        form = QuestionForm()

    return render(request, 'polls/create_question.html', {'form': form})


class QuestionListAPIView(APIView):
    """
    GET /api/questions/
    Retourne la liste de tous les sondages avec leurs choix.
    Accessible à tous (visiteur public).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        questions = Question.objects.all()
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)


class VoteAPIView(APIView):
    """
    POST /api/questions/{question_id}/vote/
    Permet à un visiteur de voter pour un choix.
    Body attendu : {"choice_id": 1}
    """
    permission_classes = [AllowAny]

    def post(self, request, question_id):
        # récupère la question ou retourne 404
        try:
            question = Question.objects.get(pk=question_id)
        except Question.DoesNotExist:
            return Response(
                {'erreur': 'Sondage introuvable'},
                status=status.HTTP_404_NOT_FOUND
            )

        # récupère le choice_id dans le body de la requête, il est également possible de le faire
        # avec choice_text.
        choice_id = request.data.get('choice_id')
        if not choice_id:
            return Response(
                {'erreur': 'Le champ choice_id est obligatoire'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # vérifie que le choix appartient bien à cette question
        try:
            choice = question.choice_set.get(pk=choice_id)
        except Choice.DoesNotExist:
            return Response(
                {'erreur': 'Ce choix n\'appartient pas à ce sondage'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # incrémente le compteur de votes et sauvegarde
        choice.votes += 1
        choice.save()

        return Response(
            {'question': question.question_text, 'choix': choice.choice_text, 'statut': 'Vote enregistré'},
            status=status.HTTP_200_OK
        )



