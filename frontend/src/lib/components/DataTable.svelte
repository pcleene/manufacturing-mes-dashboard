<script>
  let { columns = [], data = [], loading = false, emptyMessage = 'No data available' } = $props();
</script>

<div class="table-container">
  {#if loading}
    <div class="flex items-center justify-center py-8">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-OEMPartner-blue"></div>
      <span class="ml-3 text-gray-500">Loading...</span>
    </div>
  {:else if data.length === 0}
    <div class="text-center py-8 text-gray-500">
      {emptyMessage}
    </div>
  {:else}
    <table class="table">
      <thead>
        <tr>
          {#each columns as column}
            <th class="{column.align === 'right' ? 'text-right' : column.align === 'center' ? 'text-center' : ''}">
              {column.header}
            </th>
          {/each}
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        {#each data as row, index}
          <tr>
            {#each columns as column}
              <td class="{column.align === 'right' ? 'text-right' : column.align === 'center' ? 'text-center' : ''}">
                {#if column.render}
                  {@html column.render(row[column.key], row, index)}
                {:else}
                  {row[column.key] ?? '-'}
                {/if}
              </td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}
</div>
