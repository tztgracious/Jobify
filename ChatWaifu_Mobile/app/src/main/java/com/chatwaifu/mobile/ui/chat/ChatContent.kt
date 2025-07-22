package com.chatwaifu.mobile.ui.chat

import android.content.Context
import android.view.View
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.exclude
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.ime
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Autorenew
import androidx.compose.material.icons.outlined.CloseFullscreen
import androidx.compose.material.icons.outlined.Pinch
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.ScaffoldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.rememberTopAppBarState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.livedata.observeAsState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.viewmodel.compose.viewModel
import com.chatwaifu.mobile.ChatActivityViewModel
import com.chatwaifu.mobile.R
import com.chatwaifu.mobile.ui.common.ChannelNameBar
import com.chatwaifu.mobile.ui.common.InputSelector
import com.chatwaifu.mobile.ui.common.UserInput
import com.chatwaifu.mobile.ui.theme.ChatWaifu_MobileTheme
import com.chatwaifu.mobile.ui.theme.Color_55
import androidx.compose.runtime.LaunchedEffect
import kotlinx.coroutines.delay
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Button
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.remember
import android.widget.Toast
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.compose.runtime.mutableStateListOf

/**
 * Description: Chat Page
 * Author: Voine
 * Date: 2023/4/28
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatContentScaffold(
    modifier: Modifier = Modifier,
    onNavIconPressed: () -> Unit = { },
    chatTitle: String = "yuuka",
    sendMessageTitle: String = "yuuka",
    sendMessageContent: String = "example content",
    originAndroidView: (Context) -> View,
    originAndroidViewUpdate: (View) -> Unit = {},
    onSendMsgButtonClick: (String) -> Unit = {},
    onErrorOccur: (String) -> Unit = {},
    onTouchStart: () -> Unit = {},
    onTouchEnd: () -> Unit = {},
    onResetModel: () -> Unit = {},
    onRecordStart: () -> Unit = {},
    onRecordEnd: () -> Unit = {},
    chatActivityViewModel: ChatActivityViewModel
) {
    val topBarState = rememberTopAppBarState()
    val scrollBehavior = TopAppBarDefaults.pinnedScrollBehavior(topBarState)
    val vitsGenerateStatusLiveData = chatActivityViewModel.generateSoundLiveData.observeAsState()
    val chatStatusUILiveData = chatActivityViewModel.chatStatusLiveData.observeAsState()
    if (vitsGenerateStatusLiveData.value == false) {
        onErrorOccur("sound generate failed....")
    }
    val chatStatusHint = when (chatStatusUILiveData.value) {
        ChatActivityViewModel.ChatStatus.SEND_REQUEST -> {
            stringResource(id = R.string.chat_status_hint_send_request)
        }

        ChatActivityViewModel.ChatStatus.GENERATE_SOUND -> {
            stringResource(id = R.string.chat_status_hint_generate_sound)
        }

        ChatActivityViewModel.ChatStatus.TRANSLATE -> {
            stringResource(id = R.string.chat_status_hint_translate)
        }

        else -> {
            ""
        }
    }

    Scaffold(
        topBar = {
            ChannelNameBar(
                channelName = chatTitle,
                // 不传递onNavIconPressed，不显示左上角按钮
                scrollBehavior = scrollBehavior,
                externalActions = {}
            )
        },
        // Exclude ime and navigation bar padding so this can be added by the UserInput composable
        contentWindowInsets = ScaffoldDefaults
            .contentWindowInsets
            .exclude(WindowInsets.navigationBars)
            .exclude(WindowInsets.ime),
        modifier = modifier.nestedScroll(scrollBehavior.nestedScrollConnection)
    ) { paddingValues ->
        Surface(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            ChatContent(
                originAndroidView = originAndroidView,
                originAndroidViewUpdate = originAndroidViewUpdate,
                chatTitle = sendMessageTitle,
                chatContent = sendMessageContent,
                chatStatus = chatStatusHint,
                onSendMsgButtonClick = onSendMsgButtonClick,
                onTouchStart = onTouchStart,
                onTouchEnd = onTouchEnd,
                onRecordStart = onRecordStart,
                onRecordEnd = onRecordEnd,
                onResetModel = onResetModel,
                chatActivityViewModel = chatActivityViewModel // 关键参数补全
            )
        }
    }
}

@Composable
fun ChatContent(
    originAndroidView: (Context) -> View,
    originAndroidViewUpdate: (View) -> Unit = {},
    chatTitle: String = "example title",
    chatContent: String = stringResource(id = R.string.sample_very_long_str),
    chatStatus: String = "example status",
    onSendMsgButtonClick: (String) -> Unit = {},
    onTouchStart: () -> Unit = {},
    onTouchEnd: () -> Unit = {},
    onResetModel: () -> Unit = {},
    onRecordStart: () -> Unit = {},
    onRecordEnd: () -> Unit = {},
    chatActivityViewModel: ChatActivityViewModel
) {
    var touchModeEnable by rememberSaveable { mutableStateOf(false) }
    var currentInputSelector by rememberSaveable { mutableStateOf(InputSelector.NONE) }
    val isReady by chatActivityViewModel.isReady.observeAsState(false)
    val context = LocalContext.current
    // 新增：记录每个问题的答案
    val userAnswers = remember { mutableStateListOf("", "", "") }
    var currentQuestionIndex by rememberSaveable { mutableStateOf(0) }
    var showSolutionScreen by rememberSaveable { mutableStateOf(false) }

    // 监听chatActivityViewModel.currentQuestionIndex
    // 这里假设你有办法同步currentQuestionIndex
    // 你可以通过chatActivityViewModel暴露LiveData或Flow来同步

    Column(modifier = Modifier.fillMaxSize()) {
        Box(modifier = Modifier
            .weight(1f)
            .clickable(
                enabled = !touchModeEnable,
                onClick = {
                    currentInputSelector = InputSelector.NONE
                }
            ), contentAlignment = Alignment.BottomCenter) {
            AndroidView(
                modifier = Modifier.fillMaxSize(),
                factory = { context -> originAndroidView(context) },
                update = { view -> originAndroidViewUpdate(view) }
            )
            Column(modifier = Modifier) {
                if (touchModeEnable) {
                    TouchIndicator(
                        onDismissClick = {
                            touchModeEnable = false
                            onTouchEnd()
                        },
                        onResetModelClick = onResetModel
                    )
                } else {
                    Column(
                        modifier = Modifier
                            .height(200.dp)
                            .fillMaxWidth()
                            .padding(start = 20.dp, end = 20.dp, bottom = 15.dp)
                            .background(
                                color = MaterialTheme.colorScheme.tertiaryContainer.copy(alpha = 0.6f),
                                shape = MaterialTheme.shapes.medium
                            )
                    ) {
                        Text(
                            text = "$chatTitle:",
                            modifier = Modifier
                                .padding(start = 15.dp, end = 15.dp, top = 15.dp, bottom = 10.dp)
                                .fillMaxWidth(),
                            fontSize = 20.sp,
                            color = Color.White
                        )
                        Column(
                            modifier = Modifier
                                .weight(1f)
                                .padding(horizontal = 20.dp)
                                .verticalScroll(rememberScrollState())
                        ) {
                            Text(
                                text = chatContent,
                                fontSize = 14.sp,
                                color = Color.White,
                            )
                        }
                        Text(
                            text = chatStatus,
                            modifier = Modifier
                                .padding(start = 15.dp, end = 15.dp, top = 10.dp, bottom = 5.dp)
                                .fillMaxWidth(),
                            fontSize = 10.sp,
                            color = Color_55
                        )
                    }
                }
            }
            androidx.compose.material3.FloatingActionButton(
                onClick = {
                    touchModeEnable = true
                    onTouchStart()
                },
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .padding(16.dp)
            ) {
                Icon(
                    imageVector = androidx.compose.material.icons.Icons.Outlined.Pinch,
                    contentDescription = "缩放人物"
                )
            }
            if (!isReady) {
                androidx.compose.material3.Button(
                    onClick = { chatActivityViewModel.onReady() },
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(bottom = 24.dp)
                ) {
                    androidx.compose.material3.Text("Ready")
                }
            }
        }
        // 底部输入区域/Complete按钮/Solution界面
        if (isReady && !showSolutionScreen) {
            AnimatedVisibility(visible = !touchModeEnable) {
                if (currentQuestionIndex < 3) {
                    AnswerInputAreaWithTimer(
                        onSend = { answer ->
                            userAnswers[currentQuestionIndex] = answer
                            onSendMsgButtonClick(answer)
                            currentQuestionIndex++
                        },
                        enabled = true
                    )
                } else {
                    // 用白色bar包裹Complete按钮
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(Color.White)
                            .padding(16.dp)
                    ) {
                        Button(
                            onClick = {
                                val intent = android.content.Intent(context, com.chatwaifu.mobile.ui.solution.SolutionActivity::class.java)
                                intent.putStringArrayListExtra("questions", java.util.ArrayList(listOf(
                                    "Please introduce yourself and tell me about your background.",
                                    "What are your greatest strengths and how would they benefit this role?",
                                    "Describe a challenging project you worked on and how you overcame obstacles."
                                )))
                                intent.putStringArrayListExtra("answers", java.util.ArrayList(userAnswers))
                                intent.putStringArrayListExtra("solutions", java.util.ArrayList(listOf(
                                    "Fake solution 1: Try to be confident and concise.",
                                    "Fake solution 2: Highlight your teamwork and adaptability.",
                                    "Fake solution 3: Focus on problem-solving and learning from failure."
                                )))
                                context.startActivity(intent)
                            },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text("Complete")
                        }
                    }
                }
            }
        }
        if (showSolutionScreen) {
            SolutionScreen(
                questions = listOf(
                    "Please introduce yourself and tell me about your background.",
                    "What are your greatest strengths and how would they benefit this role?",
                    "Describe a challenging project you worked on and how you overcame obstacles."
                ),
                answers = userAnswers.toList(),
                solutions = listOf(
                    "Fake solution 1: Try to be confident and concise.",
                    "Fake solution 2: Highlight your teamwork and adaptability.",
                    "Fake solution 3: Focus on problem-solving and learning from failure."
                )
            )
        }
    }
}


@Composable
fun TouchIndicator(
    onDismissClick: () -> Unit = {},
    onResetModelClick: () -> Unit = {},
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 20.dp, vertical = 20.dp),
        contentAlignment = Alignment.TopEnd,
    ) {

        Column {
            Box(
                modifier = Modifier
                    .width(50.dp)
                    .height(30.dp)
                    .background(
                        MaterialTheme.colorScheme.background,
                        shape = MaterialTheme.shapes.large
                    ),
                contentAlignment = Alignment.Center
            ) {
                IconButton(
                    onClick = onDismissClick, modifier = Modifier
                ) {
                    val tint = MaterialTheme.colorScheme.primary.copy(alpha = 0.8f)
                    Icon(
                        Icons.Outlined.CloseFullscreen,
                        tint = tint,
                        modifier = Modifier
                            .size(56.dp)
                            .padding(5.dp),
                        contentDescription = null
                    )
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            Box(
                modifier = Modifier
                    .width(50.dp)
                    .height(30.dp)
                    .background(
                        MaterialTheme.colorScheme.background,
                        shape = MaterialTheme.shapes.large
                    ),
                contentAlignment = Alignment.Center
            ) {
                IconButton(
                    onClick = onResetModelClick, modifier = Modifier
                ) {
                    val tint = MaterialTheme.colorScheme.primary.copy(alpha = 0.8f)
                    Icon(
                        Icons.Outlined.Autorenew,
                        tint = tint,
                        modifier = Modifier
                            .padding(5.dp),
                        contentDescription = null
                    )
                }
            }
        }
    }
}

@Preview
@Composable
fun ChatContentPreview() {
    ChatWaifu_MobileTheme {
        val context = LocalContext.current
        ChatContent(
            originAndroidView = {
            View(context).apply {
                setBackgroundColor(resources.getColor(androidx.appcompat.R.color.material_blue_grey_800))
            }
            },
            chatActivityViewModel = androidx.lifecycle.viewmodel.compose.viewModel()
        )
    }
}


@Preview
@Composable
fun ChatContentScaffoldPreview() {
    ChatWaifu_MobileTheme {
        val context = LocalContext.current
        ChatContentScaffold(
            originAndroidView = {
                View(context).apply {
                    setBackgroundColor(resources.getColor(androidx.appcompat.R.color.material_blue_grey_800))
                }
            },
            onNavIconPressed = {},
            chatTitle = "Interviewer",
            sendMessageTitle = "Interviewer",
            sendMessageContent = "",
            onSendMsgButtonClick = {},
            onErrorOccur = {},
            onTouchStart = {},
            onTouchEnd = {},
            onResetModel = {},
            onRecordStart = {},
            onRecordEnd = {},
            chatActivityViewModel = androidx.lifecycle.viewmodel.compose.viewModel()
        )
    }
}

@Preview
@Composable
fun ChatContentScaffoldPreviewDark() {
    ChatWaifu_MobileTheme(darkTheme = true) {
        val context = LocalContext.current
        ChatContentScaffold(
            originAndroidView = {
                View(context).apply {
                    setBackgroundColor(resources.getColor(androidx.appcompat.R.color.material_blue_grey_800))
                }
            },
            onNavIconPressed = {},
            chatTitle = "Interviewer",
            sendMessageTitle = "Interviewer",
            sendMessageContent = "",
            onSendMsgButtonClick = {},
            onErrorOccur = {},
            onTouchStart = {},
            onTouchEnd = {},
            onResetModel = {},
            onRecordStart = {},
            onRecordEnd = {},
            chatActivityViewModel = androidx.lifecycle.viewmodel.compose.viewModel()
        )
    }
}

@Preview
@Composable
fun TouchIndicatorPreview() {
    TouchIndicator()
}

// 新增：带倒计时的回答区
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AnswerInputAreaWithTimer(
    onSend: (String) -> Unit,
    enabled: Boolean = true
) {
    var answerText by rememberSaveable { mutableStateOf("") }
    var timerStarted by rememberSaveable { mutableStateOf(false) }
    var timeLeft by rememberSaveable { mutableStateOf(60) } // 秒
    var inputEnabled by rememberSaveable { mutableStateOf(true) }

    // 监听输入，启动倒计时
    LaunchedEffect(answerText) {
        if (answerText.isNotBlank() && !timerStarted) {
            timerStarted = true
        }
    }

    // 倒计时逻辑
    LaunchedEffect(timerStarted, inputEnabled, enabled) {
        if (timerStarted && inputEnabled && enabled) {
            while (timeLeft > 0 && inputEnabled && enabled) {
                delay(1000)
                timeLeft -= 1
            }
            if (timeLeft == 0 && inputEnabled && enabled) {
                inputEnabled = false
                if (answerText.isNotBlank()) {
                    onSend(answerText)
                }
                // 自动提交后重置状态
                answerText = ""
                timerStarted = false
                timeLeft = 60
                inputEnabled = true
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color.White)
            .padding(16.dp)
    ) {
        if (timerStarted && inputEnabled && enabled) {
            Text("Time left: $timeLeft s", color = Color.Red)
        }
        OutlinedTextField(
            value = answerText,
            onValueChange = {
                if (inputEnabled && enabled) answerText = it
            },
            placeholder = { Text("Please enter your answer...") },
            modifier = Modifier.fillMaxWidth(),
            enabled = inputEnabled && enabled
        )
        Button(
            onClick = {
                if (answerText.isNotBlank()) {
                    onSend(answerText)
                    answerText = ""
                    timerStarted = false
                    timeLeft = 60
                    inputEnabled = true
                }
            },
            enabled = inputEnabled && enabled && answerText.isNotBlank(),
            modifier = Modifier.align(Alignment.End).padding(top = 8.dp)
        ) {
            Text("Send")
        }
    }
}

// 新增：Solution界面
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