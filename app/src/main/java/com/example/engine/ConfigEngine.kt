package com.example.engine

import android.util.Base64
import org.json.JSONObject
import java.net.URLDecoder
import java.net.URLEncoder
import java.nio.charset.StandardCharsets

object ConfigEngine {

    private val FRAGMENT_BASED_SCHEMES = listOf(
        "vless://", "trojan://", "ss://", "hysteria2://", "hy2://", "tuic://"
    )

    fun robustDecodeBase64(input: String): String {
        val trimmed = input.trim()
        val decodedBytes = try {
            Base64.decode(trimmed, Base64.DEFAULT)
        } catch (e: Exception) {
            try {
                Base64.decode(trimmed, Base64.URL_SAFE or Base64.NO_PADDING)
            } catch (e2: Exception) {
                // Manual padding append
                val paddingNeeded = (4 - (trimmed.length % 4)) % 4
                val padded = trimmed + "=".repeat(paddingNeeded)
                Base64.decode(padded, Base64.DEFAULT)
            }
        }
        return String(decodedBytes, StandardCharsets.UTF_8)
    }

    fun decodeSubscription(raw: String): List<String> {
        var content = raw.trim()
        try {
            // Check if full content is a base64 block
            val decoded = robustDecodeBase64(content)
            val lower = decoded.lowercase()
            if (lower.contains("vless://") || lower.contains("vmess://") ||
                lower.contains("trojan://") || lower.contains("ss://") ||
                lower.contains("hysteria") || lower.contains("tuic://")) {
                content = decoded
            }
        } catch (e: Exception) {
            // Not base64, parse lines directly
        }
        return content.lines()
            .map { it.trim() }
            .filter { it.isNotEmpty() }
    }

    fun renameConfig(
        config: String,
        baseName: String,
        index: Int,
        replaceKeyword: String = "",
        replaceWith: String = ""
    ): String {
        val trimmedMsg = config.trim()
        if (trimmedMsg.startsWith("vmess://", ignoreCase = true)) {
            try {
                val payload = trimmedMsg.substring("vmess://".length)
                val decodedString = robustDecodeBase64(payload)
                val json = JSONObject(decodedString)
                val currentPs = json.optString("ps", "")

                val newPs = if (replaceKeyword.isNotEmpty()) {
                    if (currentPs.contains(replaceKeyword)) {
                        currentPs.replace(replaceKeyword, replaceWith)
                    } else {
                        currentPs
                    }
                } else {
                    "$baseName-$index"
                }

                json.put("ps", newPs)
                val encodedString = Base64.encodeToString(
                    json.toString().toByteArray(StandardCharsets.UTF_8),
                    Base64.NO_WRAP
                )
                return "vmess://$encodedString"
            } catch (e: Exception) {
                return config
            }
        }

        val matchingScheme = FRAGMENT_BASED_SCHEMES.firstOrNull {
            trimmedMsg.startsWith(it, ignoreCase = true)
        }

        if (matchingScheme != null) {
            val hashIndex = trimmedMsg.indexOf('#')
            val basePart = if (hashIndex != -1) trimmedMsg.substring(0, hashIndex) else trimmedMsg
            val currentRemark = if (hashIndex != -1 && hashIndex < trimmedMsg.length - 1) {
                try {
                    URLDecoder.decode(trimmedMsg.substring(hashIndex + 1), "UTF-8")
                } catch (e: Exception) {
                    trimmedMsg.substring(hashIndex + 1)
                }
            } else {
                ""
            }

            val newRemark = if (replaceKeyword.isNotEmpty()) {
                if (currentRemark.contains(replaceKeyword)) {
                    currentRemark.replace(replaceKeyword, replaceWith)
                } else {
                    currentRemark
                }
            } else {
                "$baseName-$index"
            }

            val encodedRemark = try {
                URLEncoder.encode(newRemark, "UTF-8").replace("+", "%20")
            } catch (e: Exception) {
                newRemark
            }
            return "$basePart#$encodedRemark"
        }

        return config
    }
}
