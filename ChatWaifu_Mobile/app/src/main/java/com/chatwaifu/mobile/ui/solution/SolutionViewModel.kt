package com.chatwaifu.mobile.ui.solution

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel

class SolutionViewModel : ViewModel() {
    private val _questions = MutableLiveData<List<String>>(listOf(
        "What is polymorphism in OOP?",
        "Describe a challenging project you worked on.",
        "How do you handle tight deadlines?"
    ))
    val questions: LiveData<List<String>> = _questions

    private val _standardAnswers = MutableLiveData<List<String>>(listOf(
        "Polymorphism allows objects to be treated as instances of their parent class rather than their actual class.",
        "I worked on a cross-functional team to deliver a mobile app under a tight schedule, overcoming technical and communication challenges.",
        "I prioritize tasks, communicate clearly with stakeholders, and stay focused to meet deadlines."
    ))
    val standardAnswers: LiveData<List<String>> = _standardAnswers

    private val _yourAnswers = MutableLiveData<List<String>>(listOf(
        "It means one interface, many implementations.",
        "I built a chatbot with my classmates, we had to learn new tech quickly.",
        "I make a plan and try to finish the most important things first."
    ))
    val yourAnswers: LiveData<List<String>> = _yourAnswers
} 