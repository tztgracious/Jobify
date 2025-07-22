package com.chatwaifu.mobile.ui.solution

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

class SolutionActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val questions = intent.getStringArrayListExtra("questions") ?: arrayListOf()
        val answers = intent.getStringArrayListExtra("answers") ?: arrayListOf()
        val solutions = intent.getStringArrayListExtra("solutions") ?: arrayListOf()
        setContent {
            SolutionScreen(
                questions = questions,
                answers = answers,
                solutions = solutions
            )
        }
    }
}

@Composable
fun SolutionScreen(
    questions: List<String>,
    answers: List<String>,
    solutions: List<String>
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.White)
            .padding(24.dp)
    ) {
        Text("Interview Solutions", fontSize = 24.sp, color = Color.Black)
        Spacer(modifier = Modifier.height(16.dp))
        for (i in questions.indices) {
            Text("Q${i+1}: ${questions[i]}", fontSize = 16.sp, color = Color.DarkGray)
            Text("Your answer: ${answers.getOrNull(i) ?: ""}", fontSize = 14.sp, color = Color.Gray)
            Text("Solution: ${solutions.getOrNull(i) ?: ""}", fontSize = 14.sp, color = Color(0xFF1976D2))
            Spacer(modifier = Modifier.height(16.dp))
        }
    }
} 