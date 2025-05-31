### Btrfs: Enhanced Chunk Allocation with Device Roles, Groups, and Priority

#### Introduction
The current chunk allocator in Btrfs focuses on free space only. It works, but it doesn't give us enough control in heterogeneous setups especially when we want to manage performance, fault tolerance, or how space is consumed across devices.

This document lays out a proposal for a more flexible chunk allocation system. The idea is to let users guide chunk placement using simple policies that map better to real-world hardware setups. We reuse existing fields in `btrfs_dev_item` and introduce new semantics around roles, priorities, and device groups, with minimal impact on the on-disk format.

#### What's Broken Today
The allocator does the simplest thing: pick the device with the most free space. That's fine in uniform setups, but creates problems in more complex ones:

* **Performance bottlenecks in mixed devices**
Metadata doesn't always land on the faster devices. In an SSD + HDD setup, we want metadata on the SSD and data on the HDD. Today, we can't enforce that.

* **Awkward space usage in SINGLE/DUP**
If you're growing or shrinking a volume, the allocator might spread data across devices even when that's not what you want. There's no easy way to fill up one disk and move on to the next, or to balance across disks of uneven sizes.

* **No fault domain awareness**
RAID1 and friends protect against device failure, but not transport failures (e.g., a bad HBA). If both mirrors land on disks behind the same controller, you still lose everything.

#### Why Not Just Detect Performance?

Some might ask: why not auto-detect which device is faster?

The short answer is: it doesn't work well.

* Latency data (iostat etc.) is noisy and not reliable for permanent decisions.

* Vendor performance hints are rare and usually require out-of-band knowledge.

* In virtual setups, "rotational" might mean anything.

Instead, this design proposes letting users set device priorities explicitly. External tools can help determine these priorities at `mkfs` time or later using `btrfs properties` to make it automatic, but the key idea is: noisy iostat or guessing the device performance by type must not be used to make permanent decisions, let the admin/tools decide.

#### Device  Allocation Priority and Roles
We introduce allocation priorities. An allocation priority (1 - 255) determines the order in which devices are selected for chunk allocation. Multiple devices can share the same priority if the admin considers them to have similar performance. Lower values mean a device is more suitable for allocation; mid-range values indicate it's less preferred; and high values indicate the device must not be used at all.

At allocation time, devices are sorted by their priority, possibly adjusted by other modes. The sorting can be ascending or descending based on the chunk type. Devices are then selected from the top of the list.

For this purpose, we're reusing bits in `btrfs_dev_item::type` to track allocation preferences. Here's the layout:

```
	struct btrfs_dev_item {
		...
		union {
			__le64 type;
			struct {
				__le8 reserved[6];
				__le8 alloc_mode;     /* bits 8 - 15: mode */
				__le8 alloc_priority; /* bits 0 - 07: priority */
			};
		};
		__le32 dev_group;  /* FT device groups */
		...
	};
```

* `alloc_mode`: defines how this device participates in allocation (bitmask)
	* `FREE_SPACE`: legacy
	* `ROLE`: honor role bits
	* `PRIORITY`: use raw alloc\_priority
	* `LINEAR`: sequential allocation
	* `ROUND-ROBIN`: pick the next device
	* `FT_GROUP`: use dev\_group for fault domains

* `alloc_priority`: 1 - 255; lower means higher priority

##### Roles: Controlling What Goes Where
Device roles - such as  `metadata_only`,  `metadata`,  `data_only`,  `data`,  `both`, or  `none` - describe how a device should be used and come with predefined allocation priorities.  These guide allocation. The allocator walks through the roles in order of preference and picks the one with the most free space.

 - metadata\_only : only metadata chunks go here
 - metadata : metadata
 - preferred none || any : no preference (default)
 - data : data preferred
 - data\_only : only data chunks go here

Chunks are allocated according to a role-based order.

Ascending sort order is used for metadata chunks, prioritizing devices in the order: `metadata_only`  ->  `metadata`  -> `none` -> `data`.  
Descending sort order is used for data chunks, prioritizing devices in the order: `data_only` -> `data` -> `none` -> `metadata`.

These roles must be manually assigned, either during `mkfs` or later using `btrfs property` at runtime. Alternatively, an external tool that ranks devices by performance and passes the sorted list to `mkfs` or `btrfs property`, giving admins full control.

#### Device Groups: Fault Domain Awareness
To help with fault tolerance beyond a single Fault Tolerance connection failure, we introduce *device groups* via the `dev_item::dev_group` field.

      +-------------------------+
      |           Host          |
      +--+------------------+---+
         |                  |
     Fault Tolerance   Fault Tolerance
     Connection 1      Connection 2
          |                  |
    +-----+------+      +----+-------+
    |  Cloud     |      |  Cloud     |
    |  Storage   |      |  Storage   |
    | Device A   |      | Device C   |
    | (Low Lat)  |      | (Low Lat)  |
    | Device B   |      | Device D   |
    |(Normal Lat)|      |(Normal Lat)|
    +------------+      +------------+

Each device can be assigned a group ID (1 - 4). The allocator ensures mirrored chunks (RAID1/RAID10/RAID1C\*) are placed on devices in different groups.

This avoids putting both mirrors on disks behind the same connection.

Usage:
```
mkfs.btrfs -draid1 -mraid1 sda:ft=1 sdb:ft=1 sdc:ft=2 sdd:ft=2
```
The `dev_item::dev_group` field is used to track this on disk.

#### More Control Over Space Usage
We add new allocation strategies for SINGLE and DUP profiles:

 * **Linear allocation (by devid)**
 Fill the lowest devid until full, then move to the next. Simple, predictable. Helpful for adding temporary space.

 * **Round-robin (by_devid)**
 Distribute chunks evenly across all devices.

 * **Heterogeneous performance-aware**
 Use role-based preference: metadata to fast devices, data to slow ones. Falls back to free space when needed.

These modes let users manage their volumes more deliberately.

#### Device ID Considerations
Linear and Round-robin allocation depends on devid order. This is mostly assigned by the mkfs and kernel in the order devices are added. So it's not configurable, but in practice it's stable: devices retain their devid on replace, and new devices get the highest unused ID. We accept this limitation because the benefits are still worth it.

#### Putting It All Together

Here's what we gain from this design:
* **Better performance**
Metadata lands on SSDs or NVMe, where it belongs. Data lands on slower devices if needed.

* **Improved fault tolerance**
No more losing both mirrors to a bad cable or failed HBA or Network.

* **More control**
Admins can decide how data is spread - or not spread - across disks.

* **Minimal on-disk changes**
We reuse fields already present in `btrfs_dev_item`.

* **No magic auto-detection**
We avoid estimating device performance from noisy runtime statistics, but roles can be assigned manually or automatically using external, flexible tools.

#### Future Directions
While this proposal avoids dynamic metrics, it keeps the option open. If reliable performance hints become available - say, from a vendor API or BPF tool - they can populate `seek_speed` and `bandwidth` fields in the future.

#### Conclusion
This design gives Btrfs users more control while keeping what already works. It helps solve real-world problems like poor metadata performance, bad fault domain placement, and lack of flexibility in space usage.
Admins get tools to guide allocation at mkfs time. And we get a system that works better in the kinds of setups people actually run.
