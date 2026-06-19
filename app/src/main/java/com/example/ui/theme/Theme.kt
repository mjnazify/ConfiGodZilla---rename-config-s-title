package com.example.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val LightColorScheme = lightColorScheme(
    primary = GoldPrimary,
    onPrimary = HighDensityBackground,
    primaryContainer = GoldHover,
    secondary = HighDensityTextSecondary,
    onSecondary = HighDensityBackground,
    background = HighDensityBackground,
    onBackground = HighDensityTextPrimary,
    surface = HighDensityBackground,
    onSurface = HighDensityTextPrimary,
    outline = HighDensityOutline,
    outlineVariant = HighDensityOutlineVariant,
    surfaceVariant = HighDensityCardBg,
    onSurfaceVariant = HighDensityTextSecondary,
    error = ErrorRed,
    errorContainer = ErrorContainerRed
)

private val DarkColorScheme = darkColorScheme(
    primary = GoldPrimary,
    onPrimary = HighDensityBackground,
    primaryContainer = GoldHover,
    secondary = HighDensityTextSecondary,
    onSecondary = HighDensityBackground,
    background = HighDensityTextPrimary,
    onBackground = HighDensityBackground,
    surface = HighDensityTextPrimary,
    onSurface = HighDensityBackground,
    outline = HighDensityOutline,
    outlineVariant = HighDensityOutlineVariant,
    surfaceVariant = HighDensityDarkAccent,
    onSurfaceVariant = HighDensityBackground,
    error = ErrorRed,
    errorContainer = ErrorContainerRed
)

@Composable
fun MyApplicationTheme(
    darkTheme: Boolean = false, // Locked to beautiful gold light theme for brand alignment
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
