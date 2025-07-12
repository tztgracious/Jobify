/*
 * Copyright 2020 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.chatwaifu.mobile.ui.common

import androidx.annotation.DrawableRes
import androidx.compose.runtime.Immutable
import com.chatwaifu.mobile.R
import com.chatwaifu.mobile.ui.common.EMOJIS.EMOJI_CLOUDS
import com.chatwaifu.mobile.ui.common.EMOJIS.EMOJI_FLAMINGO
import com.chatwaifu.mobile.ui.common.EMOJIS.EMOJI_MELTING
import com.chatwaifu.mobile.ui.common.EMOJIS.EMOJI_PINK_HEART
import com.chatwaifu.mobile.ui.common.EMOJIS.EMOJI_POINTS

val initialMessages = listOf(
    Message(
        "me",
        "Check it out!",
        "8:07 PM"
    ),
    Message(
        "me",
        "Thank you!$EMOJI_PINK_HEART",
        "8:06 PM",
        R.drawable.yuuka_head
    ),
    Message(
        "Taylor Brooks",
        "You can use all the same stuff",
        "8:05 PM"
    ),
    Message(
        "Taylor Brooks",
        "@aliconors Take a look at the `Flow.collectAsStateWithLifecycle()` APIs",
        "8:05 PM"
    ),
    Message(
        "John Glenn",
        "Compose newbie as well $EMOJI_FLAMINGO, have you looked at the JetNews sample? " +
            "Most blog posts end up out of date pretty fast but this sample is always up to " +
            "date and deals with async data loading (it's faked but the same idea " +
            "applies) $EMOJI_POINTS https://goo.gle/jetnews",
        "8:04 PM"
    ),
    Message(
        "me",
        "Compose newbie: I’ve scourged the internet for tutorials about async data " +
            "loading but haven’t found any good ones $EMOJI_MELTING $EMOJI_CLOUDS. " +
            "What’s the recommended way to load async data and emit composable widgets?",
        "8:03 PM"
    )
)

val exampleUiMsg2 = listOf(
    Message(
        "me",
        "你在干嘛",
        "8:03 PM",
        isFromMe = true
    ),
    Message(
        author = "Yuuka",
        content = "在想你啊，还能干嘛",
        timestamp = "8:04 PM"
    ),
    Message(
        "me",
        "捏麻麻滴你劈我瓜是吧！",
        "8:05 PM",
        isFromMe = true
    ),
    Message(
        "Yuuka",
        "你是不是想打架！\uD83D\uDE05",
        "8:06 PM"
    )
).reversed()

val exampleUiState = ConversationUiState(
    initialMessages = initialMessages,
    channelName = "#composers",
    channelMembers = 42
)

/**
 * Example colleague profile
 */
val colleagueProfile = ProfileScreenState(
    userId = "12345",
    photo = R.drawable.yuuka_head,
    name = "Taylor Brooks",
    status = "Away",
    displayName = "taylor",
    position = "Senior Android Dev at Openlane",
    twitter = "twitter.com/taylorbrookscodes",
    timeZone = "12:25 AM local time (Eastern Daylight Time)",
    commonChannels = "2"
)

/**
 * Example "me" profile.
 */
val meProfile = ProfileScreenState(
    userId = "me",
    photo = R.drawable.atri_head,
    name = "Ali Conors",
    status = "Online",
    displayName = "aliconors",
    position = "Senior Android Dev at Yearin\nGoogle Developer Expert",
    twitter = "twitter.com/aliconors",
    timeZone = "In your timezone",
    commonChannels = null
)
@Immutable
data class Message(
    val author: String,
    val content: String,
    val timestamp: String,
    val image: Int? = null,
    val isFromMe: Boolean = false,
    val authorImage: Int = if (isFromMe) R.drawable.chat_log_person else R.drawable.yuuka_head
)

@Immutable
data class ProfileScreenState(
    val userId: String,
    @DrawableRes val photo: Int?,
    val name: String,
    val status: String,
    val displayName: String,
    val position: String,
    val twitter: String = "",
    val timeZone: String?, // Null if me
    val commonChannels: String? // Null if me
) {
    fun isMe() = userId == meProfile.userId
}

object EMOJIS {
    // EMOJI 15
    const val EMOJI_PINK_HEART = "\uD83E\uDE77"

    // EMOJI 14 🫠
    const val EMOJI_MELTING = "\uD83E\uDEE0"

    // ANDROID 13.1 😶‍🌫️
    const val EMOJI_CLOUDS = "\uD83D\uDE36\u200D\uD83C\uDF2B️"

    // ANDROID 12.0 🦩
    const val EMOJI_FLAMINGO = "\uD83E\uDDA9"

    // ANDROID 12.0  👉
    const val EMOJI_POINTS = " \uD83D\uDC49"
}
