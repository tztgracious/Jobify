package com.chatwaifu.vits.utils.text

import android.content.Context
import android.content.res.AssetManager
import android.util.Log

class EnglishTextUtils(
    override val symbols: List<String>,
    override val cleanerName: String,
    override val assetManager: AssetManager
) : TextUtils {
    private val splitSymbols = listOf(
        ".", "。","……","!","！","?","？",";","；","~","—"
    )
    override fun cleanInputs(text: String): String {
        var cleaned = text
        if (text.isNotEmpty() && splitSymbols.contains(text.last().toString())){
            cleaned = text + "\n"
        }
        return cleaned
    }

    override fun splitSentence(text: String): List<String> {
        return text.split("\n").filter { it.isNotEmpty() }
    }

    override fun convertSentenceToLabels(
        text: String
    ): List<IntArray> {
        val sentences = splitSentence(text)

        val outputs = ArrayList<IntArray>()

        var sentence = ""
        for (i in sentences.indices) {
            val s = sentences[i]
            sentence += s.split("\t")[0]
            if (s.contains("記号,読点") ||
                s.contains("記号,句点") ||
                s.contains("記号,一般") ||
                s.contains("記号,空白") ||
                i == sentences.size - 1
            ) {
                if (sentence.length > 100) {
                    throw RuntimeException("句子过长")
                }
                val labels = wordsToLabels(sentence)
                if (labels.isEmpty() || labels.sum() == 0)
                    continue
                outputs.add(labels)
                sentence = ""
            }
        }
        return outputs
    }

    override fun convertText(text: String): List<IntArray> {
        // clean inputs
        val cleanedInputs = cleanInputs(text)

        // convert inputs
        return convertSentenceToLabels(cleanedInputs)
    }

    private val cleaner = EnglishCleaners(assetManager)

    override fun wordsToLabels(text: String): IntArray {
        val labels = ArrayList<Int>()
        labels.add(0)

        // symbol to id
        val symbolToIndex = HashMap<String, Int>()
        symbols.forEachIndexed { index, s ->
            symbolToIndex[s] = index
        }

        // clean text
        var cleanedText = ""

        when (cleanerName){
            "english_cleaners" -> {
                cleanedText = cleaner.english_clean_text(text)
            }

            "english_cleaners1" -> {
                cleanedText = cleaner.english_clean_text(text)
            }

            "english_cleaners2" -> {
                cleanedText = cleaner.english_clean_text2(text)
            }
        }

        if (cleanedText.isEmpty()){
            throw RuntimeException("转换失败，请检查输入！")
        }

        // symbol to label
        for (symbol in cleanedText) {
            if (!symbols.contains(symbol.toString())) {
                continue
            }
            val label = symbolToIndex[symbol.toString()]
            if (label != null) {
                labels.add(label)
                labels.add(0)
            }
        }
        return labels.toIntArray()
    }
}