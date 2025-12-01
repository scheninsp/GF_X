# Gameframwork 对 fbx 文件的打包与加载全流程分析

## 缘起

为了解决项目中 fbx 动画资源动态加载的问题，研究了一下 Gameframework 中对资源的打包和加载流程。看看有没有什么启发。

核心都还是用的 ab 包的两大接口。AssetBundle.LoadFromFile 和 AssetBundle.LoadAssetAsync。前者直接操作文件，后者操作单个资产。

Gameframework 对于资产的管理可以分为三层抽象，资产(asset) - 文件包(Resource) - 文件系统(FileSystem)。其中文件包对应于 Unity 的ab包这个层级。

原先看Unity源码的时候可以知道，unity内部有一个 virtual file system，每个 ab 其实内部就是一个文件系统，因此才能做到对资产的快速定位和加载。而 Gameframework, YooAsset 这类打包框架，实际上就是在 ab 之上，又封装了一层 vfs。这样的好处是，ab的粒度可以分的更细，然后通过这一层封装的 vfs 进行快速加载定位，而不用受制于 unity 本身的 ab 粒度。这为完全自定义化的patch策略提供了基础。

Gameframework 在打包时，按照资产的指定分包 + 依赖关系，把资产分到不同的文件包去。在加载时，根据一个指定的资产路径，反查出他的文件包，然后从文件系统中使用 myAB = LoadFromFile(offset) 读取此文件包的分段，继而使用 myAB.LoadAssetAsync(asset) 读取资产。

对于 fbx 文件，可以把它理解成一种特殊的 prefab，内部包含了多个 gameObject(模型，骨骼),同时又包含了动画 AnimationClip。对于只包含一个 AnimationClip 的 fbx 文件，是可以通过在调用 GF 的 GF.Resource.LoadAsset 函数时，通过指定 typeof(AnimationClip) 类型，来加载出 fbx 资产中第一个，也是唯一一个 AnimationClip Object。

下面是 AI 阅读源码时的大量笔记进行的总结。不得不说 AI 现在确实是真的好用，原先可能要读几天甚至一星期的代码，现在上AI基本上2天就读个差不多了。唯一限制AI的只有Context大小了。

---

## 第一章节：打包流程总结

在此框架中，单个的源文件（如 FBX）不会被直接转换成一个独立的 `.dat` 文件。它首先被视为一个**资产（Asset）**，然后被打包进一个**资源（Resource）**，这个资源最终以 AssetBundle 的形式存在，并可能被命名为 `.dat`。

**核心关系**：
`test_anim1.fbx` 是一个资产（Asset），它被包含在名为 `DynamicAnimation.dat` 的资源（Resource）中。`DynamicAnimation.dat` 本质上是一个 Unity 的 **AssetBundle** 文件。

**打包全流程:**

1.  **资源分配 (Resource Editor)**
    *   **操作**: 在 Unity 编辑器中通过 `Game Framework/Resource Tools/Resource Editor` 打开资源编辑器。
    *   **目的**: 将 `test_anim1.fbx` 文件分配给一个特定的资源（Resource）。在这个案例中，我们将它分配到一个名为 `DynamicAnimation` 的资源组中。此配置保存在 `ResourceCollection.xml` 文件里。
    *   **关键函数**:
        *   `ResourceCollection.GetResources()`: `ResourceBuilderController` 通过此方法获取所有已定义的资源。

2.  **依赖分析 (Resource Analyzer)**
    *   **操作**: 在构建流程（Build Resources）开始时，框架会进行资产依赖分析。
    *   **目的**: 确定每个资源（Resource）需要包含哪些具体的资产（Asset）。即使 `test_anim1.fbx` 没有被其他资产（如 Prefab）依赖，由于它在第1步中被明确指定属于 `DynamicAnimation` 资源，它也会被识别并包含在内。
    *   **关键函数**:
        *   `ResourceAnalyzerController.Analyze()`: 依赖分析的入口。
        *   `AssetDatabase.GetDependencies()`: Unity 底层 API，用于获取一个资产所依赖的其他所有资产的路径。

3.  **构建 AssetBundle 列表**
    *   **操作**: 框架遍历所有需要打包的资源（Resource），为每一个资源创建一个 `AssetBundleBuild` 对象。
    *   **目的**: `AssetBundleBuild` 结构体用于告诉 Unity 应该如何打包。它包含了即将生成的 AssetBundle 名称 (`assetBundleName`) 和一个包含了所有资产路径的数组 (`assetNames`)。
    *   **过程**:
        1.  为 `DynamicAnimation` 资源创建一个 `AssetBundleBuild` 实例。
        2.  设置 `assetBundleName` 为 `dynamicAnimation.dat` (根据资源名转换)。
        3.  将 `test_anim1.fbx` 的路径添加到 `assetNames` 数组中。
    *   **关键函数**:
        *   `ResourceBuilderController.PrepareBuildData()`: 准备 `AssetBundleBuild` 数据的逻辑所在地。

4.  **执行打包**
    *   **操作**: 调用 Unity 的核心 API 来执行打包。
    *   **目的**: 根据上一步生成的 `AssetBundleBuild` 列表，在指定的输出目录（如 `AB/Working`）中创建出最终的 AssetBundle 文件。
    *   **关键函数**:
        *   `BuildPipeline.BuildAssetBundles()`: Unity 提供的核心打包函数。`ResourceBuilderController` 将 `AssetBundleBuild` 列表作为参数传递给它，最终生成 `dynamicAnimation.dat` 文件。

5.  **处理和输出 (ProcessOutput)**
    *   **操作**: 对生成的 AssetBundle 文件进行后续处理。
    *   **目的**: 根据配置（如加密、压缩、附加哈希值），将 `working` 目录下的 AB 包处理后，输出到最终的目标目录（如 `AB/Full`）。
    *   **关键函数**:
        *   `ResourceBuilderController.ProcessAssetBundle()`: 读取刚生成的 AB 包的字节。
        *   `ResourceBuilderController.ProcessOutput()`: 将字节写入到最终的文件系统中，完成打包。

---

## 第二章节：加载流程总结

加载 `test_anim1.fbx` 资产是一个两步的过程：首先加载它所在的 AssetBundle (`DynamicAnimation.dat`)，然后从这个 AssetBundle 中加载出 FBX 资产本身。

**加载全流程:**

1.  **发起加载请求 (LoadAsset)**
    *   **操作**: 业务逻辑层调用统一的加载接口。
    *   **调用**: `GF.Resource.LoadAsset("Assets/AAAGame/DynamicAnimation/test_anim1.fbx", ...)`
    *   **调用栈**:
        *   `ResourceComponent.LoadAsset()` -> `ResourceManager.LoadAsset()` -> `ResourceManager.ResourceLoader.LoadAsset()`

2.  **创建加载任务 (LoadAssetTask)**
    *   **操作**: `ResourceLoader` 内部会创建一个 `LoadAssetTask` 对象。
    *   **目的**: 此任务封装了本次加载请求的所有信息，包括要加载的资产名 (`AssetName`)、资产类型、优先级和回调函数。它还会根据资源清单确定此资产位于哪个资源（Resource）中（即 `DynamicAnimation.dat`）。
    *   **关键函数**:
        *   `LoadAssetTask.Create()`: 创建并初始化任务实例。

3.  **分配加载代理 (LoadResourceAgent)**
    *   **操作**: `ResourceLoader` 将 `LoadAssetTask` 添加到任务池 (`m_TaskPool`) 中，等待空闲的加载代理 (`LoadResourceAgent`) 来处理。
    *   **目的**: `LoadResourceAgent` 是实际执行文件 I/O 操作的单元。
    *   **关键函数**:
        *   `TaskPool<LoadResourceTaskBase>.Update()`: 任务池轮询，并分配任务给代理。
        *   `LoadResourceAgent.Start()`: 加载代理开始执行任务。

4.  **第一步：加载 AssetBundle (DynamicAnimation.dat)**
    *   **操作**: `LoadResourceAgent` 发现要加载的 FBX 资产所在的 `DynamicAnimation.dat` 资源还未被加载，于是优先加载这个资源。
    *   **目的**: 获取包含目标资产的 AssetBundle 对象。
    *   **关键函数**:
        *   `DefaultLoadResourceAgentHelper.ReadFile(fullPath)`: 辅助器调用底层 API。`fullPath` 指向 `DynamicAnimation.dat` 在磁盘上的路径。
        *   `AssetBundle.LoadFromFileAsync(fullPath)`: Unity 底层 API，异步从磁盘读取文件并创建 AssetBundle 对象。

5.  **AssetBundle 加载完成**
    *   **操作**: `LoadFromFileAsync` 完成后，`LoadResourceAgent` 会收到完成回调。
    *   **目的**: 将加载好的 AssetBundle 对象封装成一个 `ResourceObject`，并注册到资源池 (`m_ResourcePool`) 中，以备复用。
    *   **关键函数**:
        *   `LoadResourceAgent.OnLoadResourceAgentHelperReadFileComplete()`: AB 包加载完成后的回调。
        *   `ResourceObject.Create()`: 创建 `ResourceObject` 实例。

6.  **第二步：加载 FBX 资产**
    *   **操作**: `LoadAssetTask` 在其宿主 AssetBundle (`ResourceObject`) 准备好后，继续执行加载其内部具体资产的逻辑。
    *   **目的**: 从已经加载到内存的 AssetBundle 中，提取出 `test_anim1.fbx` 资产。
    *   **关键函数**:
        *   `DefaultLoadResourceAgentHelper.LoadAsset(resource, assetName, assetType, ...)`: 辅助器调用底层 API。`resource` 是上一步加载的 AssetBundle 对象。
        *   `AssetBundle.LoadAssetAsync(assetName, assetType)`: Unity 底层 API，从指定的 AssetBundle 中异步加载单个资产。`assetName` 是 FBX 的路径，`assetType` 是 `typeof(AnimationClip)`。

7.  **FBX 资产加载完成与最终回调**
    *   **操作**: `LoadAssetAsync` 完成后，`LoadResourceAgent` 再次收到完成回调。
    *   **目的**: 将加载好的资产（`AnimationClip` 对象）封装成 `AssetObject`，注册到资产池 (`m_AssetPool`)，并触发最初调用 `LoadAsset` 时传入的成功回调函数。
    *   **关键函数**:
        *   `LoadResourceAgent.OnLoadResourceAgentHelperLoadComplete()`: 资产加载完成后的回调。
        *   `AssetObject.Create()`: 创建 `AssetObject` 实例。
        *   `LoadAssetTask.OnLoadAssetSuccess()`: 调用业务层的成功回调，将加载到的 `AnimationClip` 对象传递出去，整个加载流程结束。
