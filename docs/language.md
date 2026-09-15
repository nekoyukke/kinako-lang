# kinako-lang

kinako-langの仕様について記述する

## プログラミングモデル

### Storage

`Storage` とはメモリの一部である。

### Binding

`Binding` とは `Storage` を `Type` を通じて読み出し、 `Variable` に接続することである。

### Variable

`Variable` とは、 `Value` への`Right` と `Policy` を用いた受付である

### Type

`Type` とは、 `Storage` を意味のあるものとして読みだすことのできる 金型のようなものである。

### Value

`Value` とは `Storage` を `Type` を用いて読みだした結果であり、必ず意味を持つ。

### Right

`Right` とは `Binding` の強さであり、 `Variable` からの `Storage` へのアクセスの制限を行う。

#### Ref

`Ref` は `Host` から `Right` を分割して、貸与されることである。
`Ref` 解放時に、 `Host` 群に `Right` は返却される

#### Host

`Host` とは `Storage` への最初の `Binding` を持った `Variable` である。

### Policy

`Policy` とは `Variable` から `Storage` へのアクセスのプロトコルである。

### メモリモデル

メモリモデルについて解説する。

1. すべての `Variable` は古典的スコープですべて解放される
2. すべての `Ref` は `Host` よりも `Binding` 時間が短い
3. 構造体に `Ref` を入れる場合、構造体自体が `Host` よりも短命であることを要求する。
4. `Ref` の二重は禁止。

### Record

### Interface

### Struct

### Impl

### Class

### Projection

### Allocator

### Error

### Async
