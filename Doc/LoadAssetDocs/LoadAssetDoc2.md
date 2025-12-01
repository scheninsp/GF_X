# 错误解决
hybridclr 官方 error 解决指引
https://www.hybridclr.cn/docs/help/commonerrors

```
TypeLoadException: Could not load type 'UtilityBuiltin' from assembly 'Builtin.Runtime'.
  at System.Runtime.CompilerServices.AsyncTaskMethodBuilder`1[TResult].Start[TStateMachine] (TStateMachine& stateMachine) [0x00000] in <00000000000000000000000000000000>:0 
  at System.Runtime.CompilerServices.AsyncVoidMethodBuilder.Start[TStateMachine] (TStateMachine& stateMachine) [0x00000] in <00000000000000000000000000000000>:0 
  at System.Reflection.RuntimeMethodInfo.Invoke (System.Object obj, System.Reflection.BindingFlags invokeAttr, System.Reflection.Binder binder, System.Object[] parameters, System.Globalization.CultureInfo culture) [0x00000] in <00000000000000000000000000000000>:0 
  at System.Reflection.MethodBase.Invoke (System.Object obj, System.Object[] parameters) [0x00000] in <00000000000000000000000000000000>:0 
  at LoadHotfixDllProcedure.OnUpdate (GameFramework.Fsm.IFsm`1[T] procedureOwner, System.Single elapseSeconds, System.Single realElapseSeconds) [0x00000] in <00000000000000000000000000000000>:0 
  at GameFramework.Fsm.Fsm`1[T].Update (System.Single elapseSeconds, System.Single realElapseSeconds) [0x00028] in D:\UnityProjects\GF_X\GF_X\Assets\Plugins\UnityGameFramework\GameFramework\Fsm\Fsm.cs:545 
  at GameFramework.Fsm.FsmManager.Update (System.Single elapseSeconds, System.Single realElapseSeconds) [0x0009b] in D:\UnityProjects\GF_X\GF_X\Assets\Plugins\UnityGameFramework\GameFramework\Fsm\FsmManager.cs:78 
  at GameFramework.GameFrameworkEntry.Update (System.Single elapseSeconds, System.Single realElapseSeconds) [0x0001b] in D:\UnityProjects\GF_X\GF_X\Assets\Plugins\UnityGameFramework\GameFramework\Base\GameFrameworkEntry.cs:29 
  at UnityGameFramework.Runtime.BaseComponent.Update () [0x0000b] in D:\UnityProjects\GF_X\GF_X\Assets\Plugins\UnityGameFramework\Scripts\Runtime\Base\BaseComponent.cs:231 
--- End of stack trace from previous location where exception was thrown ---

  at System.Runtime.CompilerServices.AsyncMethodBuilderCore+<>c.<ThrowAsync>b__7_0 (System.Object state) [0x00000] in <00000000000000000000000000000000>:0 
  at UnityEngine.UnitySynchronizationContext+WorkRequest.Invoke () [0x0000e] in C:\jenkins\sharedspace\ra_2022.3\Runtime\Export\Scripting\UnitySynchronizationContext.cs:153 
  at UnityEngine.UnitySynchronizationContext.Exec () [0x0005f] in C:\jenkins\sharedspace\ra_2022.3\Runtime\Export\Scripting\UnitySynchronizationContext.cs:83 
  at UnityEngine.UnitySynchronizationContext.ExecuteTasks () [0x00015] in C:\jenkins\sharedspace\ra_2022.3\Runtime\Export\Scripting\UnitySynchronizationContext.cs:107 
```

### Link.xml

   1. D:\UnityProjects\GF_X\GF_X\Assets\HybridCLRData\Generated\link.xml
   2. D:\UnityProjects\GF_X\GF_X\Assets\link.xml
   3. D:\UnityProjects\GF_X\GF_X\Assets\Plugins\UnityGameFramework\Libraries\link.xml

  其中，HybridCLRData/Generated 目录下的 link.xml 很可能是由 HybridCLR 工具自动生成的，用于防止代码在构建时被裁剪。Assets 根目录下的那个通常用于手动配置。UnityGameFramework里的则是该框架自带的。
  
重新生成了 link.xml 也没用  
  
  [Obfuz.ObfuzIgnore(Obfuz.ObfuzScope.All)]
在 public static class UtilityBuiltin 上面加这个声明可以。
Obfuz 的问题

App Builder 里关掉 Enable Obfuz
  
  
## 加 wait for managed debugger

EditorUserBuildSettings.waitForManagedDebugger 不读这个了
AppSettings.Instance.WaitForManagedDebugger  直接读这个
BuildOptions.WaitForPlayerConnection  打包加这个
构建好之后，打开游戏会弹窗问你连接


  