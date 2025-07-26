package com.chatwaifu.mobile.ui.tips

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel

class TipsViewModel : ViewModel() {
    private val _tips = MutableLiveData<List<Tip>>(listOf(
        Tip(
            title = "Prepare in Advance",
            description = "Review common interview questions and practice your answers. Research the company and the role."
        ),
        Tip(
            title = "Communicate Clearly",
            description = "Speak clearly and confidently. Structure your answers logically and avoid rambling."
        ),
        Tip(
            title = "Show Confidence",
            description = "Maintain good eye contact, smile, and show enthusiasm for the position."
        )
    ))
    val tips: LiveData<List<Tip>> = _tips

    fun generatePersonalizedTips(answers: List<String>): List<Tip> {
        val personalizedTips = mutableListOf<Tip>()
        
        // 分析答案长度
        val avgAnswerLength = answers.map { it.length }.average()
        if (avgAnswerLength < 50) {
            personalizedTips.add(Tip(
                title = "Provide More Details",
                description = "Your answers were quite brief. Try to provide more specific examples and details to demonstrate your experience."
            ))
        } else if (avgAnswerLength > 200) {
            personalizedTips.add(Tip(
                title = "Be More Concise",
                description = "Your answers were quite long. Practice being more concise while still covering key points."
            ))
        } else {
            personalizedTips.add(Tip(
                title = "Good Answer Length",
                description = "Your answers had good length. Keep this balance of detail and conciseness."
            ))
        }
        
        // 检查是否包含具体例子
        val hasExamples = answers.any { answer ->
            answer.contains("for example") || answer.contains("such as") || 
            answer.contains("specifically") || answer.contains("when")
        }
        if (!hasExamples) {
            personalizedTips.add(Tip(
                title = "Use Specific Examples",
                description = "Include specific examples from your experience to make your answers more compelling and memorable."
            ))
        } else {
            personalizedTips.add(Tip(
                title = "Great Use of Examples",
                description = "You effectively used specific examples. This helps interviewers understand your experience better."
            ))
        }
        
        // 通用建议
        personalizedTips.add(Tip(
            title = "Practice Active Listening",
            description = "Listen carefully to questions and ask for clarification if needed before answering."
        ))
        
        // 确保有3个tips
        while (personalizedTips.size < 3) {
            personalizedTips.add(Tip(
                title = "Stay Confident",
                description = "Remember to maintain confidence throughout the interview. You've prepared well!"
            ))
        }
        
        // 更新LiveData
        _tips.value = personalizedTips.take(3)
        return personalizedTips.take(3)
    }
}

data class Tip(
    val title: String,
    val description: String
) 