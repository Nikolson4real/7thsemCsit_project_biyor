import 'package:biyoar/admin/ar_example.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';
import 'package:geoflutterfire2/geoflutterfire2.dart';
import 'package:geolocator/geolocator.dart';

class HintForm extends StatelessWidget {
  HintForm({super.key});

  final GlobalKey<FormState> formKey = GlobalKey<FormState>();

  final TextEditingController _hintController = TextEditingController();
  final TextEditingController _locationHintController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Form(
          key: formKey,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              TextFormField(
                controller: _hintController,
                maxLines: 8,
                minLines: 6,
                validator: (value) {
                  if (value == null ||
                      value.isEmpty ||
                      value.replaceAll(' ', '').isEmpty) {
                    return "Cannot be empty idiot";
                  }
                },
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: "Hint",
                ),
              ),
              const SizedBox(
                height: 60,
              ),
              TextFormField(
                controller: _locationHintController,
                maxLines: 8,
                minLines: 6,
                validator: (value) {
                  if (value == null ||
                      value.isEmpty ||
                      value.replaceAll(' ', '').isEmpty) {
                    return "Cannot be empty idiot";
                  }
                },
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: "Location Hint",
                ),
              ),
              const SizedBox(
                height: 60,
              ),
              SizedBox(
                width: MediaQuery.of(context).size.width,
                child: ElevatedButton(
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (context) => CloudAnchorWidget(
                          hint: _hintController.text,
                          locationHint: _locationHintController.text,
                        ),
                      ),
                    );
                  },
                  child: const Text('Upload as Chest Hint'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

Future<void> uploadLocationhint(String hint, BuildContext context) async {
  Map<String, dynamic> data = {};
  int expiresinDays = 2;
  var expirationTime = DateTime.now().millisecondsSinceEpoch / 1000 +
      expiresinDays * 24 * 60 * 60;

  data["expirationTime"] = expirationTime;
  var currentLocation = await Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.best);

  // Add location
  GeoFirePoint myLocation = GeoFlutterFire().point(
    latitude: currentLocation.latitude,
    longitude: currentLocation.longitude,
  );
  data["position"] = myLocation.data;
  data["hint"] = hint;

  FirebaseFirestore.instance.collection('location').add(data).then(
    (value) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Location hint uploaded successfully"),
        ),
      );
    },
  );
}
