library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

-- rgb2dvi_0 包装：与原 IP 实例同名同端口，直接例化归档的 rgb2dvi 源码，
-- 便于在缺少旧 IP repository 的情况下做隔离重建（与 sobel_01/sobel_04 同一做法）。
entity rgb2dvi_0 is
    port (
        TMDS_Clk_p  : out std_logic;
        TMDS_Clk_n  : out std_logic;
        TMDS_Data_p : out std_logic_vector(2 downto 0);
        TMDS_Data_n : out std_logic_vector(2 downto 0);
        oen         : out std_logic;
        aRst_n      : in  std_logic;
        vid_pData   : in  std_logic_vector(23 downto 0);
        vid_pVDE    : in  std_logic;
        vid_pHSync  : in  std_logic;
        vid_pVSync  : in  std_logic;
        PixelClk    : in  std_logic;
        SerialClk   : in  std_logic
    );
end rgb2dvi_0;

architecture Behavioral of rgb2dvi_0 is
begin
    core : entity work.rgb2dvi
        generic map (
            kGenerateSerialClk => false,
            kClkPrimitive      => "MMCM",
            kClkRange          => 1,
            kRstActiveHigh     => false
        )
        port map (
            TMDS_Clk_p  => TMDS_Clk_p,
            TMDS_Clk_n  => TMDS_Clk_n,
            TMDS_Data_p => TMDS_Data_p,
            TMDS_Data_n => TMDS_Data_n,
            oen         => oen,
            aRst        => '0',
            aRst_n      => aRst_n,
            vid_pData   => vid_pData,
            vid_pVDE    => vid_pVDE,
            vid_pHSync  => vid_pHSync,
            vid_pVSync  => vid_pVSync,
            PixelClk    => PixelClk,
            SerialClk   => SerialClk
        );
end Behavioral;
