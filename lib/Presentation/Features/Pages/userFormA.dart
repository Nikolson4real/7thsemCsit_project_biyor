import 'package:biyoar/Core/Customs/customColors.dart';
import 'package:biyoar/Core/Customs/customElevatedButton.dart';
import 'package:biyoar/Core/Customs/customText.dart';
import 'package:biyoar/Presentation/Features/Pages/userFormResponseA.dart';
import 'package:flutter/material.dart';

class UserFormA extends StatefulWidget {
  const UserFormA({super.key});

  @override
  State<UserFormA> createState() => _UserFormAState();
}

class _UserFormAState extends State<UserFormA> {
  final _formKey = GlobalKey<FormState>();

  // Ground type options
  final List<String> groundTypes = [
    'concrete',
    'grass',
  ];
  String? selectedGroundType;

  void clearAllFields() {
    setState(() {
      selectedGroundType = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: BoxDecoration(
          image: DecorationImage(
            image: AssetImage('assets/images/biyorbgi.jpg'),
            fit: BoxFit.cover,
            colorFilter: ColorFilter.mode(
              Colors.black.withOpacity(0.3),
              BlendMode.darken,
            ),
          ),
        ),
        child: SingleChildScrollView(
          scrollDirection: Axis.vertical,
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(height: 50),

                // Back button
                Padding(
                  padding: const EdgeInsets.only(left: 20),
                  child: IconButton(
                    color: whiteColor,
                    onPressed: () {
                      Navigator.pop(context);
                    },
                    icon: Icon(Icons.arrow_back),
                    iconSize: 30,
                  ),
                ),

                SizedBox(height: 20),

                // Title
                Center(
                  child: CustomText(
                    text: "Select Ground Type",
                    color: whiteColor,
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),

                SizedBox(height: 10),

                // Subtitle
                Center(
                  child: CustomText(
                    text: "Choose the type of ground for your game",
                    color: whiteColor,
                    fontSize: 16,
                  ),
                ),

                SizedBox(height: 40),

                // Ground Type Dropdown
                SizedBox(
                  height: 70,
                  width: double.infinity,
                  child: Padding(
                    padding: const EdgeInsets.only(left: 30, right: 25, top: 5),
                    child: DropdownButtonFormField<String>(
                      value: selectedGroundType,
                      decoration: InputDecoration(
                        labelText: 'Ground Type',
                        labelStyle: TextStyle(color: greyColor, fontSize: 16),
                        filled: true,
                        fillColor: Colors.white.withOpacity(0.9),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: borderColor, width: 2),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: borderColor, width: 2),
                        ),
                        errorBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: redColor, width: 2),
                        ),
                      ),
                      dropdownColor: Colors.white,
                      items: groundTypes.map((ground) {
                        return DropdownMenuItem(
                          value: ground,
                          child: Text(
                            ground[0].toUpperCase() + ground.substring(1),
                            style: TextStyle(color: Colors.black87),
                          ),
                        );
                      }).toList(),
                      onChanged: (value) {
                        setState(() {
                          selectedGroundType = value;
                        });
                      },
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Please select a ground type';
                        }
                        return null;
                      },
                    ),
                  ),
                ),

                SizedBox(height: 40),

                // Buttons Row
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Submit Button
                    SizedBox(
                      height: 50,
                      width: 150,
                      child: CustomButton(
                        color: whiteColor,
                        borderColor: borderColor,
                        fontsize: 18,
                        onPressed: () {
                          if (!_formKey.currentState!.validate()) {
                            return;
                          }

                          // Navigate to response page with selected ground type
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => UserFormResponseA(
                                groundType: selectedGroundType!,
                              ),
                            ),
                          );
                        },
                        child: CustomText(
                          text: "Submit",
                          color: greenColor,
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),

                    // Clear Button
                    SizedBox(
                      height: 50,
                      width: 150,
                      child: CustomButton(
                        color: whiteColor,
                        borderColor: borderColor,
                        onPressed: () {
                          clearAllFields();
                        },
                        child: CustomText(
                          text: "Clear",
                          color: redColor,
                          fontSize: 18,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
