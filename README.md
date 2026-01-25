# 🛠️ Flutter Project Setup Guide

This project uses:

-   **Flutter:** `3.13.9`\
-   **FVM:** `3.2.1`\
-   **Java:** OpenJDK Corretto **11.0.29 LTS**\
-   **Java Version Manager:** SDKMAN (macOS/Linux)\
-   **Platform Support:** macOS, Windows, Linux

Follow the steps below to properly set up the development environment.

------------------------------------------------------------------------

# 📦 1. Install Java 11 (Corretto)

## macOS / Linux --- Using SDKMAN

Install SDKMAN:

``` bash
curl -s "https://get.sdkman.io" | bash
source "$HOME/.sdkman/bin/sdkman-init.sh"
```

Install the required Java version:

``` bash
sdk install java 11.0.29-amzn
sdk default java 11.0.29-amzn
```

Verify:

``` bash
java -version
```

Expected output:

    openjdk 11.0.29 2025-10-21 LTS
    OpenJDK Runtime Environment Corretto-11.0.29.7.1 (build 11.0.29+7-LTS)
    OpenJDK 64-Bit Server VM Corretto-11.0.29.7.1 (build 11.0.29+7-LTS, mixed mode)

------------------------------------------------------------------------

## Windows --- Install Java 11 (Corretto)

Use Amazon Corretto installer:\
https://docs.aws.amazon.com/corretto/latest/corretto-11-ug/downloads-list.html

Verify Java:

``` powershell
java -version
```

------------------------------------------------------------------------

# 🧩 2. Configure Flutter to Use the Same Java Version

### macOS / Linux

Add to your shell config (`~/.zshrc` or `~/.bashrc`):

``` bash
export JAVA_HOME="$HOME/.sdkman/candidates/java/current"
export PATH="$JAVA_HOME/bin:$PATH"
```

Reload:

``` bash
source ~/.zshrc 
```

### Windows

Add JAVA_HOME:

    JAVA_HOME = C:\Program Files\Amazon Corretto\jdk11.0.29

Add to PATH:

    %JAVA_HOME%\bin

Verify Flutter sees the correct Java:

``` bash
flutter doctor -v
```

------------------------------------------------------------------------

# 🐦 3. Install FVM (Flutter Version Manager)

### macOS / Linux

``` bash
dart pub global activate fvm 3.2.1
```

Add global pub to PATH:

``` bash
export PATH="$HOME/.pub-cache/bin:$PATH"
```

### Windows

In PowerShell:

``` powershell
dart pub global activate fvm 3.2.1
```

Ensure this path is added to **System PATH**:

    %USERPROFILE%\AppData\Roaming\Pub\Cache\bin

Test FVM:

``` bash
fvm --version
```

------------------------------------------------------------------------

# 🐣 4. Install Flutter 3.13.9 via FVM

Inside the project folder:

``` bash
fvm install 3.13.9
fvm use 3.13.9
```

Verify:

``` bash
fvm flutter --version
```

------------------------------------------------------------------------

# 📦 5. Get Dependencies

``` bash
fvm flutter pub get
```

------------------------------------------------------------------------

# ▶️ 6. Run the App

``` bash
fvm flutter run
```

------------------------------------------------------------------------

# 🏗️ 7. Build Commands

Android APK:

``` bash
fvm flutter build apk
```

iOS:

``` bash
fvm flutter build ios
```

Web:

``` bash
fvm flutter build web
```

------------------------------------------------------------------------

# ✔️ Setup Complete

This project is now configured to use:

-   Java 11 (Corretto)\
-   FVM-managed Flutter 3.13.9\
-   Global Dart tools\
-   Shared Java runtime across Flutter, Gradle, Android builds
