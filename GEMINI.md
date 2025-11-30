回答总是用中文输出。
这是一个 Unity 工程文件夹。

Assets\AAAGame\Scripts ，Assets\AAAGame\ScriptsBuiltin 是不可热更新的核心脚本。
 中放置着游戏脚本。其中 ScriptsBuiltin 是不可热更新的核心脚本。

启动流程
游戏通过 Assets/AAAGame/Scene/Launch.unity 这个场景进行启动。

此工程使用了 GameFramework 框架，启动脚本为 Assets\Plugins\UnityGameFramework\Scripts\Runtime\Procedure\ProcedureComponent.cs。
m_EntranceProcedureTypeName 为启动的选项，使用 LaunchProcedure，对应的脚本文件为 Assets\AAAGame\ScriptsBuiltin\Runtime\Procedures\LaunchProcedure.cs。

热更新
Assets\AAAGame\ScriptsBuiltin\Runtime\Procedures\UpdateResourcesProcedure.cs 脚本中包含了热更新资源的流程。

游戏打包使用了 Resource Mode: Updatable。也就是支持热更的打包模式。 分别使用 Build Resource 构建 ab 包，输出到 GF_X\AB\Full\1_0_0_1\Windows64。然后使用 Build App 构建应用本体，本体输出到 GF_X\BuildApp\StandaloneWindows64。

资产加载
管理加载资产的组件是 ResourceComponent, 引用在 Assets\AAAGame\ScriptsBuiltin\Runtime\Extension\GFBuiltin.cs 类的 Resource 变量。

加载资产的接口是 ResourceComponent.LoadAsset。这里会调用到 ResourceManager.cs，然后又会从 m_ResourceLoader.LoadAsset 调用到 Assets\Plugins\UnityGameFramework\GameFramework\Resource\ResourceManager.ResourceLoader.cs。

异步加载资产的任务代码在 Assets\Plugins\UnityGameFramework\GameFramework\Resource\ResourceManager.ResourceLoader.LoadAssetTask.cs。

资产加载相关的文档在 Doc\LoadAssetDocs。





