import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:intl/intl.dart';

void main() {
  runApp(const ProviderScope(child: RemotePilotApp()));
}

// --- Models ---
enum TaskStatus { IDLE, PLANNING, MODEL_CHECK, SANDBOX_SETUP, OBSERVE, ACT, VERIFY, DONE, FAILED }

class LogEntry {
  final String timestamp;
  final String agent;
  final String message;
  final String level;

  LogEntry({required this.timestamp, required this.agent, required this.message, required this.level});

  factory LogEntry.fromJson(Map<String, dynamic> json) {
    return LogEntry(
      timestamp: json['timestamp'],
      agent: json['agent'],
      message: json['message'],
      level: json['level'],
    );
  }
}

class TaskState {
  final String taskId;
  final TaskStatus status;
  final List<LogEntry> logs;
  final String goal;

  TaskState({required this.taskId, required this.status, required this.logs, required this.goal});

  TaskState copyWith({String? taskId, TaskStatus? status, List<LogEntry>? logs, String? goal}) {
    return TaskState(
      taskId: taskId ?? this.taskId,
      status: status ?? this.status,
      logs: logs ?? this.logs,
      goal: goal ?? this.goal,
    );
  }
}

// --- State Management ---
class TaskNotifier extends StateNotifier<TaskState> {
  TaskNotifier() : super(TaskState(taskId: '', status: TaskStatus.IDLE, logs: [], goal: ''));
  
  WebSocketChannel? _channel;

  void setTask(String id, String goal) {
    state = TaskState(taskId: id, status: TaskStatus.PLANNING, logs: [], goal: goal);
    _connectWebSocket();
  }

  void updateStatus(TaskStatus status) {
    state = state.copyWith(status: status);
  }

  void addLog(LogEntry log) {
    state = state.copyWith(logs: [...state.logs, log]);
  }

  void _connectWebSocket() {
    _channel?.sink.close();
    _channel = WebSocketChannel.connect(Uri.parse('ws://127.0.0.1:8000/ws/logs'));
    
    _channel!.stream.listen((message) {
      final data = jsonDecode(message);
      if (data['type'] == 'log') {
        addLog(LogEntry.fromJson(data['data']));
      } else if (data['type'] == 'state') {
        final newStatus = TaskStatus.values.firstWhere(
          (e) => e.toString().split('.').last == data['data']['status'],
          orElse: () => state.status,
        );
        updateStatus(newStatus);
      }
    });
  }
}

final taskProvider = StateNotifierProvider<TaskNotifier, TaskState>((ref) => TaskNotifier());

// --- UI Components ---
class RemotePilotApp extends StatelessWidget {
  const RemotePilotApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'RemotePilot',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blueAccent,
          brightness: Brightness.dark,
          primary: Colors.blueAccent,
          surface: const Color(0xFF1E1E1E),
        ),
        useMaterial3: true,
      ),
      home: const DashboardScreen(),
    );
  }
}

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  final TextEditingController _goalController = TextEditingController();

  Future<void> _submitTask() async {
    if (_goalController.text.isEmpty) return;
    
    final goal = _goalController.text;
    _goalController.clear();

    try {
      final response = await http.post(
        Uri.parse('http://127.0.0.1:8000/task/submit'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'goal': goal}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        ref.read(taskProvider.notifier).setTask(data['task_id'], goal);
      }
    } catch (e) {
      debugPrint("Error: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    final taskState = ref.watch(taskProvider);

    return Scaffold(
      body: Row(
        children: [
          // Left Sidebar: Status & Timeline
          Container(
            width: 300,
            color: Theme.of(context).colorScheme.surface,
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text("RemotePilot", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, letterSpacing: 1.2)),
                const SizedBox(height: 8),
                Text("V1.0.0 EXECUTION CORE", style: TextStyle(fontSize: 10, color: Colors.blueAccent.withOpacity(0.8))),
                const Divider(height: 48),
                Expanded(child: _buildTimeline(taskState.status)),
              ],
            ),
          ),
          
          // Main Body: Goal Input & Logs
          Expanded(
            child: Column(
              children: [
                // Top Bar: Goal Input
                Container(
                  padding: const EdgeInsets.all(24),
                  child: Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _goalController,
                          decoration: InputDecoration(
                            hintText: "What should I automate today?",
                            filled: true,
                            fillColor: Colors.white.withOpacity(0.05),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                            prefixIcon: const Icon(Icons.bolt, color: Colors.blueAccent),
                          ),
                          onSubmitted: (_) => _submitTask(),
                        ),
                      ),
                      const SizedBox(width: 16),
                      IconButton.filled(
                        icon: const Icon(Icons.send),
                        onPressed: _submitTask,
                        style: IconButton.styleFrom(minimumSize: const Size(60, 60)),
                      ),
                    ],
                  ),
                ),
                
                // Content: Active Goal Display & Logs
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (taskState.goal.isNotEmpty) ...[
                          Text("ACTIVE GOAL:", style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.grey[500])),
                          const SizedBox(height: 4),
                          Text(taskState.goal, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w500)),
                          const SizedBox(height: 24),
                        ],
                        const Text("EXECUTION LOGS", style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 12),
                        Expanded(child: _buildLogList(taskState.logs)),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTimeline(TaskStatus currentStatus) {
    final states = TaskStatus.values.where((s) => s != TaskStatus.IDLE).toList();
    
    return ListView.builder(
      itemCount: states.length,
      itemBuilder: (context, index) {
        final state = states[index];
        final isPassed = index < states.indexOf(currentStatus == TaskStatus.IDLE ? TaskStatus.PLANNING : currentStatus);
        final isCurrent = state == currentStatus;
        
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: Row(
            children: [
              Container(
                width: 12, height: 12,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: isCurrent ? Colors.blueAccent : (isPassed ? Colors.greenAccent : Colors.white10),
                  boxShadow: isCurrent ? [BoxShadow(color: Colors.blueAccent.withOpacity(0.5), blurRadius: 10)] : [],
                ),
              ).animate(target: isCurrent ? 1 : 0).scale(begin: const Offset(1,1), end: const Offset(1.5,1.5)).then().shake(),
              const SizedBox(width: 16),
              Text(
                state.name.replaceAll('_', ' '),
                style: TextStyle(
                  color: isCurrent ? Colors.white : (isPassed ? Colors.white70 : Colors.white24),
                  fontWeight: isCurrent ? FontWeight.bold : FontWeight.normal,
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildLogList(List<LogEntry> logs) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.black26,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white10),
      ),
      child: ListView.builder(
        reverse: true,
        padding: const EdgeInsets.all(16),
        itemCount: logs.length,
        itemBuilder: (context, index) {
          final log = logs[logs.length - 1 - index];
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  "[${_formatTime(log.timestamp)}]", 
                  style: const TextStyle(fontFamily: 'Courier', color: Colors.grey, fontSize: 12),
                ),
                const SizedBox(width: 8),
                Text(
                  log.agent.toUpperCase(), 
                  style: TextStyle(fontFamily: 'Courier', color: _getAgentColor(log.agent), fontSize: 12, fontWeight: FontWeight.bold),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    log.message, 
                    style: const TextStyle(fontFamily: 'Courier', color: Colors.white70, fontSize: 13),
                  ),
                ),
              ],
            ),
          ).animate().fadeIn().slideX(begin: 0.1, end: 0);
        },
      ),
    );
  }

  String _formatTime(String iso) {
    try {
      final dt = DateTime.parse(iso);
      return DateFormat('HH:mm:ss').format(dt);
    } catch (_) { return "00:00:00"; }
  }

  Color _getAgentColor(String agent) {
    switch (agent.toLowerCase()) {
      case 'system': return Colors.grey;
      case 'planner': return Colors.purpleAccent;
      case 'vision': return Colors.cyanAccent;
      case 'action': return Colors.orangeAccent;
      case 'verifier': return Colors.greenAccent;
      default: return Colors.blueAccent;
    }
  }
}
