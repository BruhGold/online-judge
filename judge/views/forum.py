from django.views.generic import ListView, DetailView, CreateView
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from judge.models import Topic, TopicPost

# Forum List View (Shows all topics in a forum)
class ForumTopicListView(ListView):
    model = Topic
    template_name = "forum/topic_list.html"
    context_object_name = "topics"

    def get_queryset(self):
        return Topic.objects.all().order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["content_title"] = "Topic list"
        return context

# Topic Detail View (Shows all posts inside a topic)
class ForumTopicDetailView(DetailView):
    model = Topic
    template_name = "forum/topic_detail.html"
    context_object_name = "topic"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["posts"] = self.object.posts.all().order_by("created_at")
        context["content_title"] = "Topic detail"
        return context

# Create a new Topic in a Forum
class ForumTopicCreateView(LoginRequiredMixin, CreateView):
    model = Topic
    fields = ["title"]
    template_name = "forum/new_topic.html"
    login_url = "/accounts/login/"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("forum_topic_list")
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["content_title"] = "Create New Topic"
        return context

# Create a new Post (Comment) in a Topic
class ForumTopicPostCreateView(LoginRequiredMixin, CreateView):
    model = TopicPost
    fields = ["content"]
    template_name = "forum/new_post.html"
    login_url = "/accounts/login/"

    def form_valid(self, form):
        form.instance.topic = get_object_or_404(Topic, pk=self.kwargs["pk"])
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("forum_topic_detail", kwargs={"pk": self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["topic"] = get_object_or_404(Topic, pk=self.kwargs["pk"])
        context["content_title"] = "New Post in this topic"
        return context
