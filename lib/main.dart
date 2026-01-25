import 'package:biyoar/Presentation/Features/Auth/Pages/splashscreen.dart';
import 'package:biyoar/Presentation/Features/Dashboard/userDashboard.dart';
import 'package:biyoar/Presentation/Features/Dashboard/userdash2.dart';
import 'package:biyoar/admin/ar_example.dart';
import 'package:biyoar/examples/localandwebobjectsexample.dart';
import 'package:biyoar/examples/objectgesturesexample.dart';
import 'package:biyoar/examples/objectsonplanesexample.dart';
import 'package:biyoar/test/ChickenObject.dart';
import 'package:biyoar/test/woodenChickenObject.dart';
import 'package:flutter/material.dart';
import 'dart:async';
import 'examples/screenshotexample.dart';
import 'package:flutter/services.dart';
import 'package:ar_flutter_plugin/ar_flutter_plugin.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:biyoar/Core/Services/apiService.dart';
import 'package:biyoar/Core/StateManagement/gameRulesBloc.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(MyApp());
}

class MyApp extends StatefulWidget {
  @override
  _MyAppState createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  String _platformVersion = 'Unknown';
  static const String _title = 'BiyoAR ';

  @override
  void initState() {
    super.initState();
    initPlatformState();
  }

  // Platform messages are asynchronous, so we initialize in an async method.
  Future<void> initPlatformState() async {
    String platformVersion;
    // Platform messages may fail, so we use a try/catch PlatformException.
    try {
      platformVersion = await ArFlutterPlugin.platformVersion;
    } on PlatformException {
      platformVersion = 'Failed to get platform version.';
    }

    // If the widget was removed from the tree while the asynchronous platform
    // message was in flight, we want to discard the reply rather than calling
    // setState to update our non-existent appearance.
    if (!mounted) return;

    setState(() {
      _platformVersion = platformVersion;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider<GameRulesBloc>(
          create: (context) => GameRulesBloc(ApiClient()),
        ),
      ],
      child: MaterialApp(
        title: _title,
        home: Scaffold(
          body: SplashScreen(),
        ),
        //body: SplashScreen()),
      ),
    );
    // return MaterialApp(
    //   home: Scaffold(
    //     appBar: AppBar(
    //       title: const Text(_title),
    //     ),
    //     body: Column(children: [
    //       Text('Running on: $_platformVersion\n'),
    //       Expanded(
    //         child: ExampleList(),
    //       ),
    //     ]),
    //   ),
    // );
  }
}

class ExampleList extends StatelessWidget {
  ExampleList({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text(
        "AR Plugin is initialized!\nNo example widgets loaded.",
        textAlign: TextAlign.center,
      ),
    );
  }
}
