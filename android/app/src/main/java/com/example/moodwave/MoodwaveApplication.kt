package com.example.moodwave

import android.app.Application
import com.example.moodwave.di.AppContainer
import com.example.moodwave.di.DefaultAppContainer

class MoodwaveApplication : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = DefaultAppContainer(this)
    }
}
