import 'dart:io';
import 'package:ar_flutter_plugin/managers/ar_location_manager.dart';
import 'package:ar_flutter_plugin/managers/ar_session_manager.dart';
import 'package:ar_flutter_plugin/managers/ar_object_manager.dart';
import 'package:ar_flutter_plugin/managers/ar_anchor_manager.dart';
import 'package:ar_flutter_plugin/models/ar_anchor.dart';
import 'package:ar_flutter_plugin/models/ar_hittest_result.dart';
import 'package:flutter/material.dart';
import 'package:ar_flutter_plugin/ar_flutter_plugin.dart';
import 'package:ar_flutter_plugin/datatypes/config_planedetection.dart';
import 'package:ar_flutter_plugin/datatypes/node_types.dart';
import 'package:ar_flutter_plugin/models/ar_node.dart';
import 'package:vector_math/vector_math_64.dart';
import 'package:flutter_archive/flutter_archive.dart';
import 'package:path_provider/path_provider.dart';

class ChickenObjectWidget extends StatefulWidget {
  ChickenObjectWidget({Key? key}) : super(key: key);
  @override
  ChickenObjectWidgetState createState() => ChickenObjectWidgetState();
}

class ChickenObjectWidgetState extends State<ChickenObjectWidget> {
  ARSessionManager? arSessionManager;
  ARObjectManager? arObjectManager;
  ARAnchorManager? arAnchorManager;

  ARHitTestResult? lastHitTestResult;
  ARNode? placedNode;
  ARAnchor? currentAnchor; // ✅ store last placed anchor
  HttpClient? httpClient;

  @override
  void dispose() {
    arSessionManager?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Place Object + Measure Distance')),
      body: Stack(
        children: [
          ARView(
            onARViewCreated: onARViewCreated,
            planeDetectionConfig: PlaneDetectionConfig.horizontalAndVertical,
          ),
          Align(
            alignment: Alignment.bottomCenter,
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  ElevatedButton(
                    onPressed: onPlaceObjectButtonPressed,
                    child: const Text("Place Object at Last Tap"),
                  ),
                  const SizedBox(height: 8),
                  ElevatedButton(
                    onPressed: onMeasureDistanceButtonPressed, // ✅ added
                    child: const Text("Measure Distance"),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void onARViewCreated(
    ARSessionManager arSessionManager,
    ARObjectManager arObjectManager,
    ARAnchorManager arAnchorManager,
    ARLocationManager arLocationManager,
  ) {
    this.arSessionManager = arSessionManager;
    this.arObjectManager = arObjectManager;
    this.arAnchorManager = arAnchorManager;

    this.arSessionManager!.onInitialize(
          showFeaturePoints: false,
          showPlanes: true,
          customPlaneTexturePath: "Images/triangle.png",
          showWorldOrigin: false,
          handleTaps: true,
        );

    this.arObjectManager!.onInitialize();

    this.arSessionManager!.onPlaneOrPointTap = (List<ARHitTestResult> hits) {
      if (hits.isNotEmpty) {
        setState(() {
          lastHitTestResult = hits.first;
        });
        print("✅ Tap registered on surface.");
      }
    };

    httpClient = HttpClient();
  }

  Future<void> onPlaceObjectButtonPressed() async {
    if (lastHitTestResult == null) {
      print("❌ No surface tapped yet. Tap somewhere first.");
      return;
    }

    var newAnchor =
        ARPlaneAnchor(transformation: lastHitTestResult!.worldTransform);
    bool? didAddAnchor = await arAnchorManager?.addAnchor(newAnchor);

    if (didAddAnchor == true) {
      currentAnchor = newAnchor; // ✅ save anchor for distance measurement

      var newNode = ARNode(
        type: NodeType.localGLTF2,
        uri: "Models/Chicken_01/Chicken_01.gltf",
        scale: Vector3(0.2, 0.2, 0.2),
        position: Vector3(0.0, 0.0, 0.0),
        rotation: Vector4(1.0, 0.0, 0.0, 0.0),
      );

      bool? didAddNode =
          await arObjectManager?.addNode(newNode, planeAnchor: newAnchor);

      if (didAddNode == true) {
        print("✅ Object placed successfully!");
        placedNode = newNode;
      } else {
        print("❌ Failed to add node.");
      }
    } else {
      print("❌ Failed to add anchor.");
    }
  }

  // ✅ Button callback: Measure distance from camera to current anchor
  Future<void> onMeasureDistanceButtonPressed() async {
    if (currentAnchor == null) {
      print("❌ No anchor placed yet.");
      return;
    }

    var cameraPose = await arSessionManager!.getCameraPose();

    if (cameraPose == null) {
      print("❌ Camera pose not available.");
      return;
    }

    // Extract translation components (x, y, z)
    Vector3 cameraPosition =
        Vector3(cameraPose[12], cameraPose[13], cameraPose[14]);
    Vector3 anchorPosition = Vector3(currentAnchor!.transformation[12],
        currentAnchor!.transformation[13], currentAnchor!.transformation[14]);

    // Calculate Euclidean distance
    double distance = cameraPosition.distanceTo(anchorPosition);

    print(
        "📏 Distance from camera to anchor: ${distance.toStringAsFixed(2)} meters");
  }
}
