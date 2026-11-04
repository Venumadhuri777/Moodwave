# Moodwave Android Client

Modern Android application for Spotify-style language-steerable music discovery built with Jetpack Compose, Material 3, and Kotlin Coroutines.

---

## 1. Project Specifications & Tooling
- **Target Android Studio**: Android Studio Iguana (2023.2.1) / Jellyfish (2024.1.1) or higher.
- **Gradle Version**: 8.7 (via Gradle Wrapper).
- **Android Gradle Plugin (AGP)**: 8.3.2.
- **Kotlin Version**: 1.9.23 (with KSP `1.9.23-1.0.20`).
- **Compile SDK**: `35` (Android 15).
- **Target SDK**: `35` (Android 15).
- **Min SDK**: `26` (Android 8.0 Oreo).

---

## 2. Opening the Project in Android Studio
1. Launch Android Studio.
2. Select **Open** and browse to the `/android` directory inside this project root.
3. Allow Gradle to sync dependencies via `gradle/libs.versions.toml`.
4. Ensure your local SDK path is configured in `android/local.properties` (see `local.properties.example`).

---

## 3. Running the Build Scripts

**macOS / Linux:**
```bash
./scripts/build_android.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\build_android.ps1
```

Or run directly from the `/android` directory:
```bash
./gradlew assembleDebug
```

---

## 4. Emulator Networking & BASE_URL Configuration
- **Host Loopback (`10.0.2.2`)**: The Android emulator accesses services running on the development host's `localhost` via `10.0.2.2`.
- **Debug Configuration**: `BuildConfig.BASE_URL` is set to `"http://10.0.2.2:8000/"`.
- **Release Configuration**: `BuildConfig.BASE_URL` is set to `"https://REPLACE_ME.example.com/"` (placeholder only, not used for local hackathon demo).
- **Cleartext Network Security**: `res/xml/network_security_config.xml` permits cleartext HTTP communication strictly for `10.0.2.2` and `localhost`, referenced only in `src/debug/AndroidManifest.xml`. Release builds strictly reject cleartext traffic.

---

## 5. Running Unit Tests
Unit tests use JUnit 4, Kotlin Coroutines Test, and OkHttp MockWebServer to validate network parsing, error categories, rate limit responses, and unknown key tolerance:

```bash
cd android
./gradlew testDebugUnitTest
```
