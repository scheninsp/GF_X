实例化 MyPlayer.prefab 的代码在 Assets\AAAGame\Scripts\Entity\LevelEntity.cs 文件中的 OnShow 方法里。

代码逻辑如下：
MyPlayer 这个名字出现在了数据表 AAAGame\DataTable\CombatUnitTable.txt 中。
1. 游戏流程 (MenuProcedure) 首先创建关卡实体 LevelEntity。
2. LevelEntity 在其 OnShow生命周期方法中，开始准备关卡内容。
3. 它会加载 CombatUnitTable 数据表，并获取 ID 为 0
  的那一行数据。根据我们之前的发现，这一行就是代表玩家（"MyPlayer"）的数据。
4. 最后，它调用 GF.Entity.ShowEntityAwait 方法，使用从数据表中读取到的预制体名称
  (playerRow.PrefabName，也就是 "MyPlayer") 来异步加载并创建玩家实体。
