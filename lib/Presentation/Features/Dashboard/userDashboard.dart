import 'package:biyoar/Core/Customs/customColors.dart';
import 'package:biyoar/Core/Customs/customElevatedButton.dart';
import 'package:biyoar/Core/Customs/customText.dart';
import 'package:biyoar/Presentation/Features/Pages/aboutUs.dart';
import 'package:biyoar/Presentation/Features/Pages/toolsandMaterials.dart';
import 'package:biyoar/test/ChickenObject.dart';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';

class UserDashboardScreen extends StatefulWidget {
  const UserDashboardScreen({super.key});

  @override
  _UserDashboardScreenState createState() => _UserDashboardScreenState();
}

class _UserDashboardScreenState extends State<UserDashboardScreen>
    with WidgetsBindingObserver {
  CameraController? _controller;
  Future<void>? _initializeControllerFuture;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initializeCamera(); // first time
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (_controller == null) return;

    if (state == AppLifecycleState.inactive ||
        state == AppLifecycleState.paused) {
      _controller!.dispose(); // pause camera
    } else if (state == AppLifecycleState.resumed) {
      _initializeCamera(); // resume camera smoothly
    }
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      final camera = cameras.first; // rear camera
      _controller = CameraController(
        camera,
        ResolutionPreset.medium,
        enableAudio: false,
      );
      _initializeControllerFuture = _controller!.initialize();
      await _initializeControllerFuture; // wait before setState
      if (mounted) setState(() {});
    } catch (e) {
      debugPrint("Error initializing camera: $e");
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: biyorColor,
      body: _controller == null
          ? const Center(
              child: CircularProgressIndicator(
              color: whiteColor,
            ))
          : FutureBuilder<void>(
              future: _initializeControllerFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.done) {
                  return Stack(
                    children: [
                      // ✅ Make camera fill whole screen safely
                      Positioned.fill(
                        child: FittedBox(
                          fit: BoxFit.cover,
                          child: SizedBox(
                            width: _controller!.value.previewSize!.height,
                            height: _controller!.value.previewSize!.width,
                            child: CameraPreview(_controller!),
                          ),
                        ),
                      ),

                      Column(
                        children: [
                          SizedBox(height: 70),

                          const Center(
                            child: CustomText(
                              text: "Tap Start BiyoR to begin.",
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),

                          SizedBox(height: 70),
                          //dandibiyo icon/image
                          Image.asset(
                            "assets/images/game.png",
                            height: 200,
                            width: 200,
                          ),
                          SizedBox(height: 10),
                          const Center(
                            child: CustomText(
                              text: "AR DandiBiyo",
                              fontSize: 40,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                          const Center(
                            child: CustomText(
                              text: "Reviving Tadition Through",
                              fontSize: 20,
                              //ntWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                          const Center(
                            child: CustomText(
                              text: "Argumented Reality",
                              fontSize: 20,
                              //ntWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                        ],
                      ),

                      SafeArea(
                        child: Align(
                          alignment: Alignment.bottomCenter,
                          child: Padding(
                            padding: const EdgeInsets.only(
                              bottom: 80,
                            ), // adjust spacing
                            child: Column(
                              mainAxisSize: MainAxisSize.min, // important
                              children: [
                                // Start AR button
                                SizedBox(
                                  height: 70,
                                  width:
                                      MediaQuery.of(context).size.width * 0.9,
                                  child: CustomButton(
                                    color: biyorColor.withOpacity(0.3),
                                    child: const Row(
                                      mainAxisAlignment:
                                          MainAxisAlignment.center,
                                      children: [
                                        Icon(
                                          Icons.camera_alt,
                                          color: Colors.white,
                                          size: 40,
                                        ),
                                        SizedBox(width: 10),
                                        CustomText(
                                          text: "Start BiyoR",
                                          color: Colors.white,
                                          fontSize: 30,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ],
                                    ),
                                    onPressed: () {
                                      Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                          builder: (context) =>
                                              //const StartARBiyoR(),
                                              ChickenObjectWidget(),
                                        ),
                                      ).then((_) {
                                        _initializeCamera();
                                      });
                                    },
                                  ),
                                ),

                                const SizedBox(
                                  height: 30,
                                ), // space between button and row
                                // About Game and Tools/Materials
                                Row(
                                  mainAxisAlignment:
                                      MainAxisAlignment.spaceAround,
                                  children: [
                                    Column(
                                      children: [
                                        GestureDetector(
                                          onTap: () {
                                            Navigator.push(
                                              context,
                                              MaterialPageRoute(
                                                builder: (context) =>
                                                    const ToolsMaterialsPage(),
                                              ),
                                            );
                                          },
                                          child: const Icon(
                                            Icons.settings,
                                            color: Colors.white,
                                            size: 40,
                                          ),
                                        ),
                                        const CustomText(
                                          text: "Tools/Materials",
                                          color: Colors.white,
                                          fontSize: 18,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ],
                                    ),
                                    Column(
                                      children: [
                                        GestureDetector(
                                          onTap: () {
                                            Navigator.push(
                                              context,
                                              MaterialPageRoute(
                                                builder: (context) =>
                                                    AboutUsPage(),
                                              ),
                                            );
                                          },
                                          child: const Icon(
                                            Icons.info,
                                            color: Colors.white,
                                            size: 40,
                                          ),
                                        ),
                                        const CustomText(
                                          text: "About Game",
                                          color: Colors.white,
                                          fontSize: 18,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  );
                } else if (snapshot.hasError) {
                  return Center(child: Text('Camera Error: ${snapshot.error}'));
                } else {
                  return const Center(child: CircularProgressIndicator());
                }
              },
            ),
    );
  }
}
