import os
import requests
import re
import sys

def get_wayback_snapshots(target_url):
    """
    Wayback MachineのCDX APIから指定されたURLのスナップショットを取得します。
    """
    cdx_api_url = f"http://web.archive.org/cdx/search/cdx?url={target_url}&output=text"
    
    try:
        # HTTPエラーが発生しても例外を発生させず、ステータスコードを確認
        response = requests.get(cdx_api_url, timeout=10) 
        response.raise_for_status() # 200以外のステータスコードの場合、HTTPErrorを発生させる

    except requests.exceptions.Timeout:
        print(f"Error: タイムアウトしました。URL: {cdx_api_url}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error: Wayback Machine CDX APIへのリクエスト中にエラーが発生しました: {e}")
        # レスポンスボディがあれば表示
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        return []

    lines = response.text.strip().split('\n')
    snapshots = []
    for line in lines:
        if not line:
            continue
        parts = line.split(' ')
        if len(parts) >= 3:
            timestamp = parts[1]
            original_url = parts[2]
            
            # original URLからhttp://またはhttps://を削除
            clean_original_url = re.sub(r'^https?://', '', original_url)
            snapshot_url = f"https://web.archive.org/web/{timestamp}/{clean_original_url}"
            snapshots.append({'timestamp': timestamp, 'url': snapshot_url})
            
    return snapshots

def update_readme(target_url, snapshots):
    """
    README.mdファイルにスナップショットのリストを追記します。
    """
    readme_path = "README.md"

    # README.mdの内容を準備
    markdown_heading = f"## Wayback Machine Snapshots for {target_url}"
    
    snapshot_list_content = ""
    if snapshots:
        for snapshot in snapshots:
            snapshot_list_content += f"- [{snapshot['timestamp']}]({snapshot['url']})\n"
    else:
        snapshot_list_content = "No snapshots found for this URL on Wayback Machine.\n"
    
    readme_content_to_add = f"\n---\n{markdown_heading}\n\n{snapshot_list_content}"

    # README.mdファイルが存在しない場合は作成、存在する場合は追記
    mode = 'a' if os.path.exists(readme_path) else 'w'
    with open(readme_path, mode, encoding='utf-8') as f:
        f.write(readme_content_to_add)

    # 変更があったかチェック (ここではシンプルに、ファイルに書き込んだら変更があったとみなす)
    # 厳密なチェックはGitHub Actionsのgit diffで後続ステップで行う
    return True # Pythonスクリプトからは常に変更があったと返す

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_wayback_snapshots.py <target_url>")
        sys.exit(1)
    
    target_url = sys.argv[1]
    
    print(f"Getting snapshots for: {target_url}")
    snapshots = get_wayback_snapshots(target_url)
    
    # スナップショット取得の成否に応じて、後続のActionsステップに情報を渡す
    # GITHUB_OUTPUTへの書き込みは、Actionsのrunブロック内で直接行うため、
    # Pythonスクリプトでは、更新されたかどうかの真偽値だけを返す
    
    update_readme_result = update_readme(target_url, snapshots)
    
    # GitHub Actionsのoutputsに書き込むためのフラグを設定
    # このスクリプトが呼び出されるrunブロックでこれをキャッチする
    # 例: print(f"::set-output name=changes_made::{'true' if update_readme_result else 'false'}")
    #     しかし、set-outputは非推奨なので、Actionsのシェルスクリプトでこれを処理する
    
    print(f"Successfully processed snapshots for {target_url}.")
