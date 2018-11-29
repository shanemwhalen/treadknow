import re

# example file contents
# file_contents = """
#            CPU0       CPU1       CPU2       CPU3       
#  16:          0          0          0          0  bcm2836-timer   0 Edge      arch_timer
#  17:      24279       3461      11765       5634  bcm2836-timer   1 Edge      arch_timer
#  21:          0          0          0          0  bcm2836-pmu   9 Edge      arm-pmu
#  23:       1072          0          0          0  ARMCTRL-level   1 Edge      3f00b880.mailbox
#  24:          2          0          0          0  ARMCTRL-level   2 Edge      VCHIQ doorbell
#  46:          0          0          0          0  ARMCTRL-level  48 Edge      bcm2708_fb dma
#  48:          0          0          0          0  ARMCTRL-level  50 Edge      DMA IRQ
#  50:          0          0          0          0  ARMCTRL-level  52 Edge      DMA IRQ
#  51:        403          0          0          0  ARMCTRL-level  53 Edge      DMA IRQ
#  54:       7963          0          0          0  ARMCTRL-level  56 Edge      DMA IRQ
#  59:          0          0          0          0  ARMCTRL-level  61 Edge      bcm2835-auxirq
#  62:    4147432          0          0          0  ARMCTRL-level  64 Edge      dwc_otg, dwc_otg_pcd, dwc_otg_hcd:usb1
#  86:        925          0          0          0  ARMCTRL-level  88 Edge      mmc0
#  87:          4          0          0          0  ARMCTRL-level  89 Edge      uart-pl011
#  92:      32263          0          0          0  ARMCTRL-level  94 Edge      mmc1
# 169:          0          0          0          0  lan78xx-irqs  17 Edge      usb-001:005:01
# FIQ:              usb_fiq
# IPI0:          0          0          0          0  CPU wakeup interrupts
# IPI1:          0          0          0          0  Timer broadcast interrupts
# IPI2:       7803      12661      26054       7910  Rescheduling interrupts
# IPI3:          4         10          6          8  Function call interrupts
# IPI4:          0          0          0          0  CPU stop interrupts
# IPI5:       8142        118       2129        812  IRQ work interrupts
# IPI6:          0          0          0          0  completion interrupts
#"""
def getInterrupt(interruptNum):
    with open('/proc/interrupts') as file:
        file_contents = file.read()
    
    # print file_contents
    
    lines = file_contents.strip().split("\n")
    
    re_search = re.compile("CPU")
    num_cpus = len(re.findall(re_search, lines[0]))
    
    # print num_cpus
    
    # remove first line and all lines not starting with an interrupt number
    file_contents = '\n'.join(lines[1:])
    non_numbered_exp = re.compile("^\d")
    # print re.search("^^\d", file_contents, flags=re.MULTILINE).start()
    # print file_contents[:re.search("^[^\d ]", file_contents, flags=re.MULTILINE).start()]
    
    file_contents = file_contents[:re.search("^[^\d ]", file_contents, flags=re.MULTILINE).start()]
    # print file_contents
     
    column_exp = re.compile("[^ ^\t]+(?:(?: {2,})|$)")
    
    lines = file_contents.strip(": ").split("\n")
    
    interrupts = {}
    for line in lines[:-1]:
        matches = re.findall(column_exp, line)[0:num_cpus+1]
        totalInterrupts = 0
    
        for match in matches[1:]:
            totalInterrupts = totalInterrupts + int(match.strip())
    
        interrupts[int(re.search('\d+', matches[0]).group())] = totalInterrupts
    
    # print interrupts
    
    # for int_num, vals in interrupts.iteritems():
    #     print int_num, vals 

    return interrupts[interruptNum]

