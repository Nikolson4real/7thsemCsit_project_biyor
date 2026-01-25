import 'dart:io';
import 'package:ar_flutter_plugin/managers/ar_location_manager.dart';
import 'package:ar_flutter_plugin/managers/ar_session_manager.dart';
import 'package:ar_flutter_plugin/managers/ar_object_manager.dart';
import 'package:ar_flutter_plugin/managers/ar_anchor_manager.dart';
import 'package:ar_flutter_plugin/models/ar_anchor.dart';
import 'package:ar_flutter_plugin/models/ar_hittest_result.dart';
import 'package:biyoar/Core/Customs/customColors.dart';

import 'package:flutter/material.dart';
import 'package:ar_flutter_plugin/ar_flutter_plugin.dart';
import 'package:ar_flutter_plugin/datatypes/config_planedetection.dart';
import 'package:ar_flutter_plugin/datatypes/node_types.dart';
import 'package:ar_flutter_plugin/models/ar_node.dart';
import 'package:vector_math/vector_math_64.dart' as vm;

/// Small container to tie a node with its anchor (so we can remove either later)
class PlacedItem {
  final ARNode node;
  final ARAnchor anchor;
  vm.Vector4 rotation;

  PlacedItem({
    required this.node,
    required this.anchor,
    required this.rotation,
  });
}

class ChickenObjectWidget extends StatefulWidget {
  @override
  ChickenObjectWidgetState createState() => ChickenObjectWidgetState();
}

class ChickenObjectWidgetState extends State<ChickenObjectWidget> {
  ARSessionManager? arSessionManager;
  ARObjectManager? arObjectManager;
  ARAnchorManager? arAnchorManager;
  ARHitTestResult? lastHitTestResult;
  HttpClient? httpClient;

  // multi-object storage
  final List<PlacedItem> placedItems = [];

  // optional: index of currently selected item for measuring/removing
  int? selectedIndex;
  double? measuredDistance;

  //features toogle
  bool showARFeatures = false;

  @override
  void dispose() {
    arSessionManager?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      //appBar: AppBar(title: const Text('Multi-place Object + Measure'),backgroundColor: biyorColor   ,),

      body: Stack(
        children: [
          ARView(
            onARViewCreated: onARViewCreated,
            planeDetectionConfig: PlaneDetectionConfig.horizontal,
          ),
          Positioned(
            top: 30, // adjust if needed
            left: 20,
            child: SafeArea(
              child: IconButton(
                icon: const Icon(Icons.arrow_back, color: whiteColor, size: 30),
                onPressed: () => Navigator.pop(context),
              ),
            ),
          ),
          Align(
            alignment: Alignment.bottomCenter,
            child: Padding(
              padding: const EdgeInsets.all(12.0),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.start,
                    children: [
                      IconButton(
                        icon: Icon(showARFeatures ? Icons.close : Icons.menu,
                            color: whiteColor, size: 30),
                        onPressed: () {
                          setState(() {
                            showARFeatures = !showARFeatures;
                          });
                        },
                      ),
                    ],
                  ),

                  // placement buttons
                  Visibility(
                    visible: showARFeatures,
                    child: Row(
                      children: [
                        Expanded(
                          child: ElevatedButton(
                            // style: ElevatedButton.styleFrom(
                            //   backgroundColor: biyorColor
                            // ) ,
                            style: translucentButtonStyle,
                            onPressed: () =>
                                onPlaceObjectButtonPressed('chicken'),
                            child: const Text("Place Chicken"),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: ElevatedButton(
                            style: translucentButtonStyle,
                            onPressed: () =>
                                onPlaceObjectButtonPressed('ground'),
                            child: const Text("Place Ground"),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: ElevatedButton(
                            style: translucentButtonStyle,
                            onPressed: onRemoveLastPressed,
                            child: const Text("Remove Last"),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 8),

                  Visibility(
                    visible: showARFeatures,
                    child: Row(
                      children: [
                        Expanded(
                          child: ElevatedButton(
                            style: translucentButtonStyle,
                            onPressed: onRemoveAllPressed,
                            child: const Text("Clear All"),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: ElevatedButton(
                            style: translucentButtonStyle,
                            onPressed: onMeasureToLastPressed,
                            child: const Text("Measure → Last"),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: ElevatedButton(
                            style: translucentButtonStyle,
                            onPressed: onMeasureToSelectedPressed,
                            child: const Text("Measure → Selected"),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 12),

                  // show status: count, selected index, distance
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        "Objects: ${placedItems.length}",
                        style: TextStyle(color: whiteColor),
                      ),
                      const SizedBox(width: 12),
                      Text(
                        "Selected: ${selectedIndex == null ? '-' : selectedIndex}",
                        style: TextStyle(color: whiteColor),
                      )
                    ],
                  ),

                  const SizedBox(height: 8),

                  Visibility(
                    visible: showARFeatures,
                    child: Row(
                      children: [
                        Expanded(
                          child: ElevatedButton(
                            style: translucentButtonStyle,
                            onPressed: () => _rotateSelected(-10),
                            child: const Text("Rotate ⟲ Left"),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: ElevatedButton(
                            style: translucentButtonStyle,
                            onPressed: () => _rotateSelected(10),
                            child: const Text("Rotate ⟳ Right"),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 8),

                  if (measuredDistance != null)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          vertical: 8, horizontal: 16),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        "📏 Distance: ${measuredDistance!.toStringAsFixed(2)} m",
                        style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: whiteColor),
                      ),
                    ),

                  const SizedBox(height: 8),

                  // optional small list to pick an item to measure/remove by index
                  if (placedItems.isNotEmpty)
                    SizedBox(
                      height: 56,
                      child: ListView.separated(
                        scrollDirection: Axis.horizontal,
                        itemBuilder: (context, idx) {
                          final selected = selectedIndex == idx;
                          return GestureDetector(
                            onTap: () {
                              setState(() {
                                selectedIndex = idx;
                              });
                            },
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 12, vertical: 8),
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(8),
                                // color: selected ? Colors.blue.withOpacity(0.8) : Colors.grey.withOpacity(0.2),
                              ),
                              child: Center(child: Text("Item #$idx")),
                            ),
                          );
                        },
                        separatorBuilder: (_, __) => const SizedBox(width: 8),
                        itemCount: placedItems.length,
                      ),
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

    arSessionManager.onInitialize(
      showFeaturePoints: false,
      showPlanes: true,
      customPlaneTexturePath: "Images/triangle.png",
      showWorldOrigin: false,
      handleTaps: true,
    );

    arObjectManager.onInitialize();

    arSessionManager.onPlaneOrPointTap = (List<ARHitTestResult> hits) {
      if (hits.isNotEmpty) {
        setState(() {
          lastHitTestResult = hits.first;
        });
        print("✅ Tap registered on surface.");
      }
    };

    httpClient = HttpClient();
  }

  Future<void> onPlaceObjectButtonPressed(String objectType) async {
    if (lastHitTestResult == null) {
      print("❌ No surface tapped yet. Tap somewhere first.");
      return;
    }

    // create anchor at tap
    var newAnchor =
        ARPlaneAnchor(transformation: lastHitTestResult!.worldTransform);
    bool? didAddAnchor = await arAnchorManager?.addAnchor(newAnchor);

    if (didAddAnchor != true) {
      print("❌ Failed to add anchor.");
      return;
    }

    // prepare node for the chosen type
    ARNode newNode;
    if (objectType == 'chicken') {
      newNode = ARNode(
        type: NodeType.localGLTF2,
        uri: "Models/Chicken_01/Chicken_01.gltf",
        scale: vm.Vector3(0.2, 0.2, 0.2),
        position: vm.Vector3(0.0, 0.0, 0.0),
        rotation: vm.Vector4(1.0, 0.0, 0.0, 0.0),
      );
    } else {
      newNode = ARNode(
        type: NodeType.localGLTF2,
        uri: "Models/Beachcourt/scene.gltf",
        //uri: "Models/BiyorField/biyorfield.gltf",
        scale: vm.Vector3(0.2, 0.2, 0.2),
        position: vm.Vector3(0.0, 0.0, 0.0),
        rotation: vm.Vector4(1.0, 0.0, 0.0, 0.0),
      );
    }

    bool? didAddNode =
        await arObjectManager?.addNode(newNode, planeAnchor: newAnchor);

    if (didAddNode == true) {
      // store both node & anchor together
      placedItems.add(
        PlacedItem(
          node: newNode,
          anchor: newAnchor,
          rotation: vm.Vector4(0, 1, 0, 0), // Y-axis, angle = 0
        ),
      );

      // auto-select the newly placed item
      selectedIndex = placedItems.length - 1;
      print("✅ Object placed successfully! Total: ${placedItems.length}");
      setState(() {});
    } else {
      // cleanup anchor if node couldn't be added
      await arAnchorManager?.removeAnchor(newAnchor);
      print("❌ Failed to add node - cleaned up anchor.");
    }
  }

  Future<void> onRemoveLastPressed() async {
    if (placedItems.isEmpty) {
      print("❌ Nothing to remove.");
      return;
    }

    final last = placedItems.removeLast();

    // remove node first, then anchor (safe order)
    bool? removedNode = await arObjectManager?.removeNode(last.node);
    if (removedNode == true) {
      print("🗑️ Removed node.");
    } else {
      print("❌ Failed to remove node.");
    }

    bool? removedAnchor = await arAnchorManager?.removeAnchor(last.anchor);
    if (removedAnchor == true) {
      print("🗑️ Removed anchor.");
    } else {
      print("❌ Failed to remove anchor.");
    }

    // adjust selected index
    if (placedItems.isEmpty) {
      selectedIndex = null;
    } else {
      selectedIndex = placedItems.length - 1;
    }

    setState(() {});
  }

  Future<void> onRemoveAllPressed() async {
    if (placedItems.isEmpty) {
      print("❌ Nothing to remove.");
      return;
    }

    // remove all nodes/anchors
    for (final item in List<PlacedItem>.from(placedItems)) {
      await arObjectManager?.removeNode(item.node);
      await arAnchorManager?.removeAnchor(item.anchor);
    }

    placedItems.clear();
    selectedIndex = null;
    print("🗑️ All objects removed.");
    setState(() {});
  }

  Future<void> onMeasureToLastPressed() async {
    if (placedItems.isEmpty) {
      print("❌ No objects to measure to.");
      return;
    }

    final lastAnchor = placedItems.last.anchor;
    await _measureDistanceToAnchor(lastAnchor);
  }

  Future<void> onMeasureToSelectedPressed() async {
    if (selectedIndex == null) {
      print(
          "❌ No selected object. Tap an item in the small list to select it.");
      return;
    }
    if (selectedIndex! < 0 || selectedIndex! >= placedItems.length) {
      print("❌ Selected index out of range.");
      return;
    }
    final anchor = placedItems[selectedIndex!].anchor;
    await _measureDistanceToAnchor(anchor);
  }

  // helper: compute distance between camera and anchor transform
  Future<void> _measureDistanceToAnchor(ARAnchor anchor) async {
    var cameraPose = await arSessionManager!.getCameraPose();
    if (cameraPose == null) {
      print("❌ Camera pose not available.");
      return;
    }

    vm.Vector3 cameraPosition =
        vm.Vector3(cameraPose[12], cameraPose[13], cameraPose[14]);

    vm.Vector3 anchorPosition = vm.Vector3(anchor.transformation[12],
        anchor.transformation[13], anchor.transformation[14]);

    double distance = cameraPosition.distanceTo(anchorPosition);
    measuredDistance = distance;
    print("📏 Distance to anchor: ${distance.toStringAsFixed(2)} m");
    setState(() {});
  }

  Future<void> _rotateSelected(double degrees) async {
    if (selectedIndex == null) {
      print("❌ No object selected.");
      return;
    }

    final item = placedItems[selectedIndex!];
    final node = item.node;

    // convert degree to radians
    double radians = degrees * 3.1415926535 / 180.0;

    // extract current rotation from the node’s transform matrix
    final currentRotation = node.eulerAngles; // Vector3

    // apply rotation around Y-axis
    final newRotation = vm.Vector3(
      currentRotation.x + radians,
      currentRotation.y,
      currentRotation.z,
    );

    // assign new rotation
    node.eulerAngles = newRotation;

    // force notifier update
    node.transformNotifier.value = node.transformNotifier.value;

    print("🔄 Rotated selected object by $degrees degrees.");
    setState(() {});
  }

  final ButtonStyle translucentButtonStyle = ElevatedButton.styleFrom(
    backgroundColor: biyorColor.withOpacity(0.30),
    foregroundColor: whiteColor,
    elevation: 0,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(10),
    ),
  );
}
